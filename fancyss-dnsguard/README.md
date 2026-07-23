# fancyss DNS Guard IPQ32

面向 ASUS ZenWiFi BD4（IPQ5322 / ARMv7 / `fancyss_ipq32_full`）的 DNS 防劫持增强。

基于：

- fancyss 3.5.30
- 上游提交：`b19e82cb6a05e08990a96905353921819d44d134`
- 本地功能提交：`d58c597ca59157241fbc3e191d6b19814346c9a8`
- 官方 IPQ32 Full 基础包 MD5：`5519268d19fa1895456b19a4a03032d7`

## 功能

- 标准模式：自动切换 SmartDNS，国内和国外均使用加密 DoT 上游。
- 强制接管局域网客户端 TCP/UDP 53。
- 阻止 IPv4、IPv6 明文 DNS 外泄。
- 严格模式额外封锁路由器自身向 WAN 发出的明文 53。
- 固定引导 IP，启动加密 DNS 前不依赖明文域名解析。
- 关闭、重启或卸载 fancyss 时沿用其防火墙生命周期自动清理规则。

## 获取源码

当前目录保存了可直接应用到官方 fancyss 源码的完整提交补丁：

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

文件名：`fancyss_ipq32_full_dnsguard-3.5.30-test1.tar.gz`

SHA-256：

```text
5ea88402fc46468f7ac76a0edcf2f4d1ca7745e68f06addd91bbcf26e8ba6c35
```

这是实机测试版。首次建议只开启“标准模式”，确认 BD4 联网、节点解析和 IPv6 均正常后，再尝试严格模式。

## 回滚

在 fancyss DNS 设置中把“防运营商 DNS 劫持”切换为“关闭”并应用。禁用或卸载 fancyss 也会清理 DNS Guard 的 `SHADOWSOCKS*` 防火墙链。
