#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
import re
import socketserver
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler
from typing import Any


DEFAULT_SOURCE = os.environ.get("DEFAULT_SOURCE_URL", "")
DIRECT_RULES_FILE = os.environ.get("DIRECT_RULES_FILE", "/data/direct-rules.txt")
TEST_URL = "http://www.gstatic.com/generate_204"
INTERVAL = 300
TOLERANCE = 50

REGIONS = [
    ("HK", re.compile(r"(港|香港|HK|Hong Kong|HongKong|HKG)", re.I)),
    ("TW", re.compile(r"(台|台湾|臺灣|TW|Taiwan|Taipei)", re.I)),
    ("JP", re.compile(r"(日|日本|JP|Japan|Tokyo|Osaka|东京|大阪)", re.I)),
    ("SG", re.compile(r"(新加坡|狮城|SG|Singapore)", re.I)),
    ("US", re.compile(r"(美|美国|US|USA|United States|Los Angeles|San Jose|Silicon Valley|Seattle|New York|洛杉矶|圣何塞|西雅图|纽约)", re.I)),
    ("KR", re.compile(r"(韩|韩国|KR|Korea|Seoul|首尔)", re.I)),
]

RULES = [
    "DOMAIN,invite.linuxdo.org,DIRECT",
    "DOMAIN-SUFFIX,kuakeba.cn,DIRECT",
    "DOMAIN-KEYWORD,ysu.edu.cn,DIRECT",
    "DOMAIN-SUFFIX,bing.com,DIRECT",
    "DOMAIN-SUFFIX,hltv.org,DIRECT",
    "DOMAIN-SUFFIX,aminer.cn,DIRECT",
    "DOMAIN-KEYWORD,bangumi,DIRECT",
    "DOMAIN-SUFFIX,kuafuzy.com,DIRECT",
    "DOMAIN-SUFFIX,steamserver.net,DIRECT",
    "DOMAIN-KEYWORD,ysu.edu,DIRECT",
    "DOMAIN-KEYWORD,microsoft,DIRECT",
    "DOMAIN,auth1.ysu.edu.cn,DIRECT",
    "DOMAIN-SUFFIX,ysu.edu.cn,DIRECT",
    "DOMAIN,ss0.baidu.com,DIRECT",
    "DOMAIN-SUFFIX,ruijie.com.cn,DIRECT",
    "IP-CIDR,124.124.124.124/32,DIRECT,no-resolve",
    "DOMAIN-SUFFIX,local,国内直连",
    "DOMAIN-SUFFIX,localhost,国内直连",
    "DOMAIN-SUFFIX,lan,国内直连",
    "IP-CIDR,10.0.0.0/8,国内直连,no-resolve",
    "IP-CIDR,100.64.0.0/10,国内直连,no-resolve",
    "IP-CIDR,127.0.0.0/8,国内直连,no-resolve",
    "IP-CIDR,169.254.0.0/16,国内直连,no-resolve",
    "IP-CIDR,172.16.0.0/12,国内直连,no-resolve",
    "IP-CIDR,192.168.0.0/16,国内直连,no-resolve",
    "DOMAIN-SUFFIX,openai.com,OpenAI",
    "DOMAIN-SUFFIX,chatgpt.com,OpenAI",
    "DOMAIN-SUFFIX,oaistatic.com,OpenAI",
    "DOMAIN-SUFFIX,oaiusercontent.com,OpenAI",
    "DOMAIN-SUFFIX,t.me,Telegram",
    "DOMAIN-SUFFIX,telegram.org,Telegram",
    "DOMAIN-SUFFIX,telegram.me,Telegram",
    "DOMAIN-SUFFIX,telegra.ph,Telegram",
    "IP-CIDR,91.108.4.0/22,Telegram,no-resolve",
    "IP-CIDR,91.108.8.0/22,Telegram,no-resolve",
    "IP-CIDR,91.108.12.0/22,Telegram,no-resolve",
    "IP-CIDR,91.108.16.0/22,Telegram,no-resolve",
    "IP-CIDR,91.108.56.0/22,Telegram,no-resolve",
    "IP-CIDR,149.154.160.0/20,Telegram,no-resolve",
    "DOMAIN-SUFFIX,youtube.com,YouTube",
    "DOMAIN-SUFFIX,ytimg.com,YouTube",
    "DOMAIN-SUFFIX,googlevideo.com,YouTube",
    "DOMAIN-SUFFIX,youtu.be,YouTube",
    "DOMAIN-SUFFIX,youtubei.googleapis.com,YouTube",
    "DOMAIN-SUFFIX,netflix.com,Netflix",
    "DOMAIN-SUFFIX,netflix.net,Netflix",
    "DOMAIN-SUFFIX,nflxext.com,Netflix",
    "DOMAIN-SUFFIX,nflximg.net,Netflix",
    "DOMAIN-SUFFIX,nflxvideo.net,Netflix",
    "DOMAIN-SUFFIX,disneyplus.com,国外媒体",
    "DOMAIN-SUFFIX,apple.com,苹果服务",
    "DOMAIN-SUFFIX,icloud.com,苹果服务",
    "DOMAIN-SUFFIX,cdn-apple.com,苹果服务",
    "DOMAIN-SUFFIX,mzstatic.com,苹果服务",
    "DOMAIN-SUFFIX,cn,国内直连",
    "DOMAIN-SUFFIX,baidu.com,国内直连",
    "DOMAIN-SUFFIX,qq.com,国内直连",
    "DOMAIN-SUFFIX,weixin.qq.com,国内直连",
    "DOMAIN-SUFFIX,taobao.com,国内直连",
    "DOMAIN-SUFFIX,tmall.com,国内直连",
    "DOMAIN-SUFFIX,jd.com,国内直连",
    "DOMAIN-SUFFIX,alipay.com,国内直连",
    "DOMAIN-SUFFIX,aliyun.com,国内直连",
    "DOMAIN-SUFFIX,bilibili.com,国内直连",
    "DOMAIN-SUFFIX,zhihu.com,国内直连",
    "DOMAIN-SUFFIX,douyin.com,国内直连",
    "DOMAIN-SUFFIX,bytedance.com,国内直连",
    "DOMAIN-SUFFIX,kuaishou.com,国内直连",
    "DOMAIN-SUFFIX,163.com,国内直连",
    "DOMAIN-SUFFIX,126.net,国内直连",
    "DOMAIN-SUFFIX,netease.com,国内直连",
    "DOMAIN-SUFFIX,weibo.com,国内直连",
    "DOMAIN-SUFFIX,sina.com.cn,国内直连",
    "DOMAIN-SUFFIX,csdn.net,国内直连",
    "DOMAIN-SUFFIX,gitee.com,国内直连",
    "MATCH,漏网之鱼",
]


def load_rules() -> list[str]:
    if DIRECT_RULES_FILE and os.path.exists(DIRECT_RULES_FILE):
        with open(DIRECT_RULES_FILE, "r", encoding="utf-8") as fp:
            rules = [line.strip() for line in fp if line.strip() and not line.lstrip().startswith(("#", ";"))]
        return rules
    return list(RULES)


def save_rules(text: str) -> list[str]:
    rules = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith(("#", ";"))]
    directory = os.path.dirname(DIRECT_RULES_FILE)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(DIRECT_RULES_FILE, "w", encoding="utf-8") as fp:
        fp.write("\n".join(rules) + ("\n" if rules else ""))
    return rules


def fetch_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "mihomo-converter/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def maybe_base64_decode(data: bytes) -> str:
    text = data.decode("utf-8", "replace").strip()
    if "://" in text:
        return text
    compact = re.sub(r"\s+", "", text)
    padded = compact + "=" * (-len(compact) % 4)
    try:
        decoded = base64.b64decode(padded, validate=False).decode("utf-8", "replace")
    except Exception:
        return text
    return decoded if "://" in decoded else text


def truthy(value: str | None) -> bool:
    return value in {"1", "true", "True", "yes", "YES"}


def unique_name(name: str, seen: dict[str, int]) -> str:
    name = name.strip() or "未命名节点"
    if name not in seen:
        seen[name] = 1
        return name
    seen[name] += 1
    return f"{name} {seen[name]}"


def parse_vless(line: str, seen: dict[str, int]) -> dict[str, Any] | None:
    parsed = urllib.parse.urlsplit(line)
    if not parsed.hostname or not parsed.username:
        return None
    query = {k: v[-1] for k, v in urllib.parse.parse_qs(parsed.query, keep_blank_values=True).items()}
    name = unique_name(urllib.parse.unquote(parsed.fragment), seen)
    proxy: dict[str, Any] = {
        "name": name,
        "type": "vless",
        "server": parsed.hostname,
        "port": parsed.port or 443,
        "uuid": urllib.parse.unquote(parsed.username),
        "network": query.get("type", "tcp") or "tcp",
        "udp": True,
    }
    flow = query.get("flow")
    if flow:
        proxy["flow"] = flow
    security = query.get("security", "")
    if security in {"tls", "reality"}:
        proxy["tls"] = True
        proxy["servername"] = query.get("sni") or query.get("peer") or query.get("host") or parsed.hostname
        if security == "reality":
            proxy["reality-opts"] = {
                "public-key": query.get("pbk", ""),
                "short-id": query.get("sid", ""),
            }
        fp = query.get("fp")
        if fp:
            proxy["client-fingerprint"] = fp
    if truthy(query.get("insecure")):
        proxy["skip-cert-verify"] = True
    if proxy["network"] == "ws":
        proxy["ws-opts"] = {
            "path": urllib.parse.unquote(query.get("path", "") or "/"),
            "headers": {"Host": query.get("host") or query.get("sni") or parsed.hostname},
        }
    return proxy


def parse_hysteria2(line: str, seen: dict[str, int]) -> dict[str, Any] | None:
    parsed = urllib.parse.urlsplit(line)
    if not parsed.hostname or not parsed.username:
        return None
    query = {k: v[-1] for k, v in urllib.parse.parse_qs(parsed.query, keep_blank_values=True).items()}
    name = unique_name(urllib.parse.unquote(parsed.fragment), seen)
    proxy: dict[str, Any] = {
        "name": name,
        "type": "hysteria2",
        "server": parsed.hostname,
        "port": parsed.port or 443,
        "password": urllib.parse.unquote(parsed.username),
        "sni": query.get("sni", ""),
        "skip-cert-verify": truthy(query.get("insecure")),
    }
    mport = query.get("mport")
    if mport:
        proxy["ports"] = mport
    return proxy


def parse_nodes(subscription_text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen: dict[str, int] = {}
    proxies: list[dict[str, Any]] = []
    info_proxies: list[dict[str, Any]] = []
    for raw in subscription_text.splitlines():
        line = raw.strip()
        if not line or "://" not in line:
            continue
        scheme = line.split(":", 1)[0].lower()
        if scheme == "vless":
            proxy = parse_vless(line, seen)
        elif scheme in {"hysteria2", "hy2"}:
            proxy = parse_hysteria2(line, seen)
        else:
            proxy = None
        if not proxy:
            continue
        if is_subscription_info(proxy["name"]):
            info_proxies.append({"name": proxy["name"], "type": "direct", "udp": True})
        else:
            proxies.append(proxy)
    return proxies, info_proxies


def is_subscription_info(name: str) -> bool:
    return bool(re.search(r"(剩余流量|距离下次|套餐到期|官网|网址|产品|到期时间)", name))


def region_names(proxies: list[dict[str, Any]], regex: re.Pattern[str]) -> list[str]:
    return [p["name"] for p in proxies if regex.search(p["name"])]


def other_names(proxies: list[dict[str, Any]]) -> list[str]:
    out = []
    for proxy in proxies:
        if not any(regex.search(proxy["name"]) for _, regex in REGIONS):
            out.append(proxy["name"])
    return out


def group(name: str, group_type: str, proxies: list[str], **extra: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"name": name, "type": group_type, "proxies": proxies}
    item.update(extra)
    return item


def health_group(name: str, group_type: str, proxies: list[str]) -> dict[str, Any]:
    return group(name, group_type, proxies, url=TEST_URL, interval=INTERVAL, tolerance=TOLERANCE)


def build_groups(proxies: list[dict[str, Any]], info_proxies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all_names = [p["name"] for p in proxies]
    groups: list[dict[str, Any]] = []
    region_group_names: list[str] = []

    for code, regex in REGIONS:
        names = region_names(proxies, regex)
        if names:
            groups.append(health_group(code, "url-test", names))
            region_group_names.append(code)

    other = other_names(proxies)
    if other:
        groups.append(health_group("其他节点", "url-test", other))
        region_group_names.append("其他节点")

    groups.insert(0, group("节点选择", "select", region_group_names + ["DIRECT"] + all_names))
    if info_proxies:
        groups.insert(0, group("订阅信息", "select", [p["name"] for p in info_proxies] + ["DIRECT"]))

    def policy_members(preferred: list[str], *, direct: bool = False, direct_first: bool = False) -> list[str]:
        members = [name for name in preferred if name in region_group_names]
        if direct_first:
            return ["DIRECT", "节点选择"] + members
        members.append("节点选择")
        if direct:
            members.append("DIRECT")
        return members

    groups.extend(
        [
            group("OpenAI", "select", policy_members(["JP", "US", "SG", "HK"], direct=True)),
            group("Telegram", "select", policy_members(["SG", "HK", "JP", "US"])),
            group("YouTube", "select", policy_members(["HK", "JP", "SG", "US"])),
            group("Netflix", "select", policy_members(["HK", "JP", "SG", "US"])),
            group("国外媒体", "select", policy_members(["HK", "JP", "SG", "US"])),
            group("微软服务", "select", policy_members(["HK", "JP", "SG"], direct_first=True)),
            group("苹果服务", "select", policy_members(["HK", "JP"], direct_first=True)),
            group("国内直连", "select", ["DIRECT", "节点选择"]),
            group("广告拦截", "select", ["REJECT", "DIRECT"]),
            group("漏网之鱼", "select", ["节点选择", "DIRECT"]),
        ]
    )
    return groups


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def dump_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if value is None:
        return "null"
    if isinstance(value, str):
        if value == "" or re.search(r"[:#{}\[\],&*?|\-<>=!%@`'\"]|\s", value):
            return yaml_quote(value)
        return value
    return yaml_quote(str(value))


def dump_yaml(value: Any, indent: int = 0) -> list[str]:
    lines: list[str] = []
    prefix = " " * indent
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {dump_scalar(item)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{prefix}-")
                lines.extend(dump_yaml(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{prefix}-")
                lines.extend(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {dump_scalar(item)}")
    return lines


def convert(source_url: str) -> str:
    raw = fetch_url(source_url)
    text = maybe_base64_decode(raw)
    proxies, info_proxies = parse_nodes(text)
    doc = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": True,
        "mode": "Rule",
        "log-level": "info",
        "external-controller": "127.0.0.1:9090",
        "proxies": info_proxies + proxies,
        "proxy-groups": build_groups(proxies, info_proxies),
        "rules": load_rules(),
    }
    return "\n".join(dump_yaml(doc)) + "\n"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}", file=sys.stderr)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/version":
            self.send_text("mihomo-converter local\n", "text/plain; charset=utf-8")
            return
        if parsed.path == "/direct-rules":
            self.send_json({"rules": load_rules()})
            return
        if parsed.path != "/sub":
            self.send_error(404)
            return
        query = urllib.parse.parse_qs(parsed.query)
        source_url = query.get("url", [DEFAULT_SOURCE])[0] or DEFAULT_SOURCE
        if not source_url:
            self.send_error(400, "missing subscription url")
            return
        try:
            body = convert(source_url).encode("utf-8")
        except Exception as exc:
            self.send_error(502, f"conversion failed: {exc}")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/yaml; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="mihomo.yaml"')
        self.send_cors_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path != "/direct-rules":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length).decode("utf-8")
            data = json.loads(payload) if payload else {}
            rules = save_rules(str(data.get("text", "")))
        except Exception as exc:
            self.send_error(400, f"invalid rules payload: {exc}")
            return
        self.send_json({"rules": rules})

    def send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")

    def send_json(self, data: Any) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_cors_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, text: str, content_type: str) -> None:
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_cors_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    with socketserver.ThreadingTCPServer(("0.0.0.0", 25600), Handler) as server:
        server.daemon_threads = True
        server.serve_forever()


if __name__ == "__main__":
    main()
