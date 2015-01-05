Transparent-proxy
=================

VPN tunnel always slow than proxies that use Hybla as tcp congestion.  Use a transparent proxy to enable Hybla for VPN tunnel too.
pptp openvpn 等 VPN 方案相对于启用 Hybla 后的代理方案（如 shadowsocks），明显存在 tcp 速率更慢的问题。这是由于与海外网站建立的连接都是高延迟的，这种环境下默认的TCP拥塞控制算法 cubic 并不合适。


RHEL6 上使用方法：

1. 安装 pip 及其依赖项 python-setuptools ，然后所有python包可以简单的通过pip安装
    yum install python-setuptools

    wget https://pypi.python.org/packages/source/p/pip/pip-1.5.6.tar.gz

    tar -xf pip-1.5.6.tar.gz
    cd pip-1.5.6
    python setup.py install

2. 安装 tornado

    pip install tornado


3. 修改系统配置 /etc/sysctl.conf，增大网络缓存并启用 Hybla。增加如下配置
    net.core.wmem_max=12582912
    net.core.rmem_max=12582912
    net.ipv4.tcp_rmem= 10240 87380 12582912
    net.ipv4.tcp_wmem= 10240 87380 12582912

    net.ipv4.tcp_congestion_control = hybla

 然后使配置生效
    sysctl -p



4. 设置NAT规则。编辑 /etc/sysconfig/iptables, 在 nat 节点的 :OUTPUT 行下增加
    *nat
    :PREROUTING ACCEPT [0:0]
    :POSTROUTING ACCEPT [0:0]
    :OUTPUT ACCEPT [0:0]

    # Accelerate pptp
    -A PREROUTING ! -d 10.0.0.0/8 -i ppp+ -p tcp -m multiport --dports 80,443  -j REDIRECT --to-ports 8888

 然后重启 iptables
    /etc/init.d/iptables restart

5. 启动 tcp_proxy.py
    nohup python tcp_proxy.py &

 想开机自启动，可以把上面的命令，加到 /etc/rc.local 上





