#!/usr/bin/env python3
"""Check declared module ownership and dependencies before implementation exists."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    target: str
    message: str


def unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"重复 JSON 键：{key}")
        result[key] = value
    return result


def text_value(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} 必须是非空字符串")
    return value


def path_value(value: Any, field: str) -> str:
    text_value(value, field)
    path = PurePosixPath(value)
    if (path.is_absolute() or value == "." or ".." in path.parts
            or "\\" in value or ":" in value or str(path) != value):
        raise ContractError(f"{field} 必须是规范的仓库内相对路径，不能是根目录：{value}")
    return value


def string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ContractError(f"{field} 必须是列表")
    for item in value:
        text_value(item, field)
    if len(set(value)) != len(value):
        raise ContractError(f"{field} 包含重复项")
    return value


def fields(value: Any, required: set[str], optional: set[str], field: str) -> None:
    if not isinstance(value, dict):
        raise ContractError(f"{field} 必须是对象")
    missing = required - value.keys()
    extra = value.keys() - required - optional
    if missing or extra:
        raise ContractError(f"{field} 字段错误；缺少 {sorted(missing)}；未知 {sorted(extra)}")


def validate(data: Any) -> None:
    fields(data, {"version", "modules", "resources"}, {"note"}, "design")
    if type(data["version"]) is not int or data["version"] != 1:
        raise ContractError("version 必须为 1")
    if "note" in data:
        text_value(data["note"], "note")
    modules = data["modules"]
    if not isinstance(modules, dict) or not modules:
        raise ContractError("modules 必须是非空对象")
    module_paths = set()
    for name, item in modules.items():
        text_value(name, "module id")
        fields(item, {"path", "purpose", "owns", "decides", "depends_on"},
               {"entrypoint", "independent_reason"}, name)
        path = path_value(item["path"], f"{name}.path")
        if path in module_paths:
            raise ContractError(f"两个模块使用同一路径：{path}")
        module_paths.add(path)
        text_value(item["purpose"], f"{name}.purpose")
        for key in ("owns", "decides"):
            string_list(item[key], f"{name}.{key}")
        if "entrypoint" in item and type(item["entrypoint"]) is not bool:
            raise ContractError(f"{name}.entrypoint 必须是布尔值")
        if "independent_reason" in item:
            text_value(item["independent_reason"], f"{name}.independent_reason")
        if not isinstance(item["depends_on"], list):
            raise ContractError(f"{name}.depends_on 必须是列表")
        seen = set()
        for edge in item["depends_on"]:
            fields(edge, {"module", "contract"}, set(), f"{name}.depends_on")
            target = text_value(edge["module"], f"{name}.depends_on.module")
            if target not in modules:
                raise ContractError(f"{name} 依赖未声明模块：{target}")
            if target in seen:
                raise ContractError(f"重复依赖：{name} → {target}")
            seen.add(target)
            if not isinstance(edge["contract"], str):
                raise ContractError(f"{name} → {target} 的 contract 必须是字符串")
    resources = data["resources"]
    if not isinstance(resources, dict):
        raise ContractError("resources 必须是对象（没有待检查材料时写 {}）")
    resource_paths = set()
    for name, item in resources.items():
        text_value(name, "resource id")
        fields(item, {"path", "owner", "consumers"},
               {"shared_reason", "maintainer"}, f"resource {name}")
        path = path_value(item["path"], f"{name}.path")
        if path in resource_paths:
            raise ContractError(f"重复资源路径：{path}")
        resource_paths.add(path)
        owner = item["owner"]
        if owner is not None and (not isinstance(owner, str) or owner not in modules):
            raise ContractError(f"{name} 的 owner 必须是已声明模块或 null")
        consumers = string_list(item["consumers"], f"{name}.consumers")
        if set(consumers) - modules.keys():
            raise ContractError(f"{name} 有未声明的业务消费者：{sorted(set(consumers) - modules.keys())}")
        for key in ("shared_reason", "maintainer"):
            if key in item and not isinstance(item[key], str):
                raise ContractError(f"{name}.{key} 必须是字符串")


def within(path: str, parent: str) -> bool:
    return PurePosixPath(path).is_relative_to(PurePosixPath(parent))


def find_cycles(nodes: list[str], edges: list[dict[str, str]]) -> list[list[str]]:
    # Retained from the original checker: strongly connected components.
    graph = {node: [] for node in nodes}
    for edge in edges:
        graph[edge["from"]].append(edge["to"])
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indexes[node] = lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in graph[node]:
            if target not in indexes:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[target])
        if indexes[node] == lowlinks[node]:
            group = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                group.append(member)
                if member == node:
                    break
            if len(group) > 1:
                cycles.append(sorted(group))

    for node in nodes:
        if node not in indexes:
            visit(node)
    return sorted(cycles)


def analyze(data: dict, root: Path | None = None) -> list[Finding]:
    """root enables optional on-disk checks; no root is needed for a design."""
    validate(data)
    findings: list[Finding] = []

    def add(level: str, code: str, target: str, message: str) -> None:
        findings.append(Finding(level, code, target, message))

    modules = data["modules"]
    incoming: dict[str, set[str]] = {name: set() for name in modules}
    edges = []
    for name, item in modules.items():
        if not item["owns"] and not item["decides"]:
            add("warning", "EMPTY_RESPONSIBILITY", name, "没有声明事实或决定；核对是否只是技术分层或实现细节。")
        for edge in item["depends_on"]:
            target = edge["module"]
            edges.append({"from": name, "to": target})
            incoming[target].add(name)
            if target == name:
                add("error", "SELF_DEPENDENCY", name, "模块内部调用不应声明为跨模块依赖。")
            if not edge["contract"].strip():
                add("error", "MISSING_CONTRACT", f"{name} → {target}", "说明依赖的公开能力或事实，不能只画一条边。")
    for key in ("owns", "decides"):
        owners: dict[str, list[str]] = {}
        for name, item in modules.items():
            for responsibility in item[key]:
                owners.setdefault(responsibility, []).append(name)
        for responsibility, assigned in owners.items():
            if len(assigned) > 1:
                add("error", "DUPLICATE_AUTHORITY", responsibility,
                    f"{key} 同时归属 {', '.join(assigned)}；明确唯一权威或区分不同语义/派生视图。")
    for group in find_cycles(list(modules), edges):
        add("error", "DEPENDENCY_CYCLE", ", ".join(group), "循环依赖：检查是否拆错边界，或需要收窄契约；不要只改箭头。")
    for name, consumers in incoming.items():
        item = modules[name]
        if item.get("entrypoint"):
            continue
        if not consumers:
            add("warning", "NO_CONSUMER", name, "没有声明消费者或外部入口；核对独立存在的依据，不要编造依赖。")
        elif len(consumers) == 1:
            consumer = next(iter(consumers))
            if consumer != name and not within(item["path"], modules[consumer]["path"]):
                reason = item.get("independent_reason", "尚未给出独立变化依据")
                add("warning", "SINGLE_CONSUMER_MODULE", name,
                    f"唯一调用者为 {consumer}；比较合并/内部子模块/保留独立边界。声明依据：{reason}。需业务判断。")
    for name, item in data["resources"].items():
        owner, consumers, path = item["owner"], item["consumers"], item["path"]
        if not consumers:
            add("warning", "UNUSED_RESOURCE", name, "没有真实业务使用者；核对是否需要这项设计。")
        elif len(consumers) == 1:
            sole = consumers[0]
            if owner != sole or not within(path, modules[sole]["path"]):
                add("error", "SINGLE_CONSUMER_EXTERNAL", name,
                    f"仅 {sole} 使用，应归属并放入 {modules[sole]['path']}/ 内，当前为 {path}。")
        if owner is not None:
            if not within(path, modules[owner]["path"]):
                add("error", "OWNER_LOCATION", name, f"归属 {owner} 的材料应放在该模块内，当前为 {path}。")
            for consumer in consumers:
                if consumer != owner and owner not in {e["module"] for e in modules[consumer]["depends_on"]}:
                    add("error", "UNDECLARED_CONSUMPTION", name,
                        f"{consumer} 消费 {owner} 的材料却没有公开依赖契约；核对是否穿透内部。")
        elif len(consumers) > 1:
            if not item.get("shared_reason", "").strip() or not item.get("maintainer", "").strip():
                add("error", "UNJUSTIFIED_SHARED", name, "共享须说明当前共同语义、共享理由及维护责任。")
            else:
                add("warning", "SHARED_REVIEW", name, "多个消费者与理由只构成候选证据；人工核对语义一致、范围最小及变化影响。")
    if root is not None:
        root = root.resolve()
        for name, item in list(modules.items()) + list(data["resources"].items()):
            path = (root / item["path"]).resolve()
            if not path.is_relative_to(root):
                add("error", "PATH_ESCAPE", name, "实际路径通过符号链接超出仓库。")
            elif not path.exists():
                add("error", "MISSING_PATH", name, f"实现核对时路径不存在：{item['path']}")
    return findings


def cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def report(data: dict, findings: list[Finding]) -> str:
    errors = sum(f.level == "error" for f in findings)
    warnings = sum(f.level == "warning" for f in findings)
    lines = ["# 模块设计声明检查", "", f"机械检查：{errors} 项错误，{warnings} 项待评审提示。",
             "", "> 只核对输入声明，不扫描源码，不证明事实/规则完整或设计合理；尚未创建目录也可检查。",
             "> 业务场景、独立变化理由、未声明内容和证据真实性仍需人工评审。", ""]
    if data.get("note"):
        lines += [cell(data["note"]), ""]
    lines += ["## 发现", "", "| 级别 | 规则 | 对象 | 判断与修改方向 |", "| --- | --- | --- | --- |"]
    for finding in findings:
        lines.append("| " + " | ".join(cell(v) for v in (finding.level, finding.code, finding.target, finding.message)) + " |")
    if not findings:
        lines.append("| — | — | — | 未发现机械错误；不能据此宣布设计通过。 |")
    lines += ["", "## 声明的业务依赖", "", "箭头 A → B 表示 A 使用 B 的公开能力或事实。共享机制的消费者另见材料归属表。", "", "| 消费者 | 提供者 | 公开契约 |", "| --- | --- | --- |"]
    for name, item in data["modules"].items():
        for edge in item["depends_on"]:
            lines.append(f"| {cell(name)} | {cell(edge['module'])} | {cell(edge['contract'])} |")
    lines += ["", "## 材料归属", "", "| 内容 | 路径 | 所有者 | 业务使用者 |", "| --- | --- | --- | --- |"]
    for name, item in data["resources"].items():
        lines.append(f"| {cell(name)} | {cell(item['path'])} | {cell(item['owner'] or '共享候选')} | {cell(', '.join(item['consumers']))} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--design", type=Path, default=Path("architecture/module-design.json"))
    parser.add_argument("--output", default=".reports/module-design.md", help="相对 root 的报告路径，或 - 输出到终端")
    parser.add_argument("--check-only", action="store_true", help="显示发现，不写报告")
    parser.add_argument("--check-paths", action="store_true", help="实现阶段才核对路径存在；默认只检查设计")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    design_path = args.design if args.design.is_absolute() else root / args.design
    try:
        data = json.loads(design_path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        findings = analyze(data, root if args.check_paths else None)
        if args.check_only:
            for finding in findings:
                print(f"{finding.level} {finding.code} [{finding.target}]: {finding.message}")
            print(f"机械检查：{sum(f.level == 'error' for f in findings)} 错误，"
                  f"{sum(f.level == 'warning' for f in findings)} 待评审；不代表设计已通过。")
        elif args.output == "-":
            sys.stdout.write(report(data, findings))
        else:
            output = Path(args.output)
            if not output.is_absolute():
                output = root / output
            if output.resolve() == design_path.resolve():
                raise ContractError("报告不能覆盖设计声明")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(report(data, findings), encoding="utf-8")
            print(f"报告：{output}")
        return 1 if any(f.level == "error" for f in findings) else 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"module-design: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
