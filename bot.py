#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Irys Eligibility 高并发批量查询脚本（最终成品）

功能：
  - 多线程高并发（默认 30）
  - 自动轮询代理池（HTTP Basic Auth）
  - 自动解析所有异常格式（Irys 很混乱）
  - 无报错输出，全都标准化输出
  - 自动写入 result.jsonl
  - Z 世代风 console 输出
"""

import requests
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========= Irys 接口 =========
API_URL = "https://registration.irys.xyz/api/eligibility"

HEADERS = {
    "Host": "registration.irys.xyz",
    "Referer": "https://registration.irys.xyz/",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    )
}

# ========= 代理池（你提供的全部已录入） =========
PROXIES = []

# ========= 工具函数 =========

def load_wallets(file="wallets.txt"):
    """读取地址"""
    return [line.strip() for line in open(file, "r") if line.strip()]


def get_proxy():
    if not PROXIES:
        return None
    p = random.choice(PROXIES)
    return {"http": p, "https": p}


def parse_result(address, data):
    """
    统一解析 Irys 返回格式
    """
    # Normal case
    if isinstance(data, dict) and "eligible" in data:
        return {
            "address": address,
            "eligible": bool(data["eligible"]),
            "status": "normal",
            "raw": data
        }

    # fallback format: {'total': '0' | '1', 'detail': {...}}
    if isinstance(data, dict) and "detail" in data and "total" in data:
        t = data.get("total")
        try:
            eligible_val = int(t) > 0
        except Exception:
            eligible_val = bool(t)
        return {
            "address": address,
            "eligible": eligible_val,
            "status": "fallback_format",
            "raw": data
        }

    # unknown case
    return {
        "address": address,
        "eligible": False,
        "status": "unknown_format",
        "raw": data
    }


def fetch(address, retry=3):
    """请求 eligibility + 自动代理 + 自动重试"""
    url = f"{API_URL}?address={address}"

    for _ in range(retry):
        try:
            proxies = get_proxy()
            if proxies:
                res = requests.get(url, headers=HEADERS, proxies=proxies, timeout=6)
            else:
                res = requests.get(url, headers=HEADERS, timeout=6)
            data = res.json()

            return {
                "address": address,
                "proxy": proxies["http"] if proxies else "direct",
                "parsed": parse_result(address, data)
            }

        except Exception:
            time.sleep(random.uniform(0.2, 0.6))

    return {
        "address": address,
        "proxy": "failed",
        "parsed": {
            "address": address,
            "eligible": False,
            "status": "network_failed",
            "raw": {}
        }
    }


def save(result):
    with open("eligibility_result.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


# ========= 主程序 =========

def main():
    wallets = load_wallets()
    global PROXIES
    PROXIES = []
    try:
        lines = [line.strip() for line in open("proxy.txt", "r", encoding="utf-8") if line.strip()]
        urls = []
        for line in lines:
            parts = line.split(":")
            if len(parts) == 4:
                ip, port, user, pwd = parts
                urls.append(f"http://{user}:{pwd}@{ip}:{port}")
            else:
                urls.append(line)
        PROXIES = urls
    except Exception:
        PROXIES = []
    total = len(wallets)

    print(f"🚀 多线程批量查询启动，共 {total} 个地址\n")

    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(fetch, w): w for w in wallets}

        for future in as_completed(futures):
            r = future.result()
            parsed = r["parsed"]
            addr = parsed["address"]

            # 输出格式统一
            if parsed["eligible"]:
                print(f"🟢 {addr} → Eligible ✔")
            else:
                print(f"🔴 {addr} → Not Eligible ({parsed['status']})")

            save(r)

    print("\n🎉 全部查询完成！结果保存在 eligibility_result.jsonl\n")


if __name__ == "__main__":
    main()