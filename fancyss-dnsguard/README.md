# fancyss DNS Guard IPQ32

面向 ASUS ZenWiFi BD4（IPQ5322 / ARMv7 / `fancyss_ipq32_full`）的 DNS 防劫持增强。

基于：

- fancyss 3.5.30
- 上游提交：`b19e82cb6a05e08990a96905353921819d44d134`
- DNS Guard 初始提交：`d58c597ca59157241fbc3e191d6b19814346c9a8`
- DoH 优先升级提交：`f7235b1a70b17ef68f82a09550abe9f783e4d3d4`
- 官方 IPQ32 Full 基础包 MD5：`5519268d19fa1895456b19a4a03032d7`

## 功能

- 标准模式自动切换 SmartDNS。
- DoH 443 作为主用加密上游，DoT 853 作为故障备用。
- 国内组直连阿里 DNS、DNSPod；国外组通过当前 fancyss 代理访问 Cloudflare、Google。
- 所有加密上游使用固定引导 IP，启动前不依赖运营商明文 DNS。
- 强制接管局域网客户端 TCP/UDP 53。
- 阻止 IPv4、IPv6 明文 DNS 外泄。
- 严格模式额外封锁路由器自身向 WAN 发出的明文 53。
- 关闭、重启或卸载 fancyss 时沿用其防火墙生命周期自动清理规则。

## 获取源码

当前目录保存了可直接应用到官方 fancyss 3.5.30 源码的连续提交补丁：

```bash
git clone https://github.com/hq450/fancyss.git
cd fancyss
git checkout b19e82cb6a05e08990a96905353921819d44d134
git am ../0001-fancyss-dnsguard-ipq32.patch
```

应用补丁后运行：

```bash
./tests/test_dns_guard.sh
./build_dns_guard_ipq32.sh
```

构建脚本使用官方 `packages/fancyss_ipq32_full.tar.gz` 作为完整基础包，把修改后的 WebUI、SmartDNS 和防火墙逻辑合并进去；安装期间不会联网下载组件。

## 当前测试包

文件名：`fancyss_ipq32_full_dnsguard-3.5.30-doh-test2.tar.gz`

SHA-256：

```text
08c6f097aaed154fc9d0eec77a8b964bbee87a8b5fb31356c354cc3705467a1c
```

MD5：

```text
2987e90b2bcfe956e0f9e59d716afdd9
```

这是 IPQ32 实机测试版。安装后进入“软件中心 → fancyss → DNS 设置 → 其它 DNS 相关设置”，先选择“标准模式（推荐）”。确认 BD4 联网、节点解析和 IPv6 均正常后，再尝试严格模式。

## 回滚

在 fancyss DNS 设置中把“防运营商 DNS 劫持”切换为“关闭”并应用。禁用或卸载 fancyss 也会清理 DNS Guard 的 `SHADOWSOCKS*` 防火墙链。
