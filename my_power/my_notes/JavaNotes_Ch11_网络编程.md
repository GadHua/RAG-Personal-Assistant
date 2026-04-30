# Ch11 - Java 网络编程

## 摘要

> 本章系统讲解 Java 网络编程的完整知识体系：从经典的 OSI 与 TCP/IP 模型出发，深入 TCP 三次握手四次挥手的底层原理与状态流转，再到 HTTP/HTTPS 协议的请求结构、状态码和 SSL/TLS 机制；然后进入 Socket 编程，涵盖 TCP/UDP 的 ServerSocket/Socket/DatagramSocket 用法与常见坑；随后升级到 NIO 的 Channel/Buffer/Selector 多路复用模型；最后进入高性能网络框架 Netty，讲解 Bootstrap、ChannelHandler、ByteBuf、EventLoop 等核心组件，并剖析 TCP 粘包半包、长连接保活、异步 I/O 等高级主题。全文配以完整代码示例，帮助读者建立从"理解协议"到"熟练 Socket"再到"掌握高性能网络编程"的完整技能栈。

---

## 11.1 网络编程概述

### 11.1.1 网络体系结构：OSI 七层模型

**OSI（Open Systems Interconnection）模型**是国际标准化组织（ISO）提出的网络通信标准参考模型，将网络通信划分为七层，每层职责明确，层与层之间通过接口通信：

| 层级 | 名称 | 职责 | 典型协议/技术 | Java 相关 |
|------|------|------|-------------|----------|
| 7 | 应用层（Application） | 为用户提供网络服务接口 | HTTP、FTP、SMTP、DNS | `java.net.URL`、`HttpURLConnection` |
| 6 | 表示层（Presentation） | 数据格式转换、加密解密 | TLS/SSL、JPEG、ASCII | `SSLSocket`、`javax.crypto` |
| 5 | 会话层（Session） | 管理会话建立、维护、终止 | NetBIOS、RPC | `Socket`、`Session` |
| 4 | 传输层（Transport） | 端到端可靠传输、流量控制 | **TCP**、**UDP** | `ServerSocket`、`Socket`、`DatagramSocket` |
| 3 | 网络层（Network） | IP 寻址、路由转发 | **IP**、ICMP、Router | `InetAddress`、`InetSocketAddress` |
| 2 | 数据链路层（Data Link） | 帧同步、差错控制 | Ethernet、PPP、MAC | NIC Driver |
| 1 | 物理层（Physical） | 比特流传输 | 光纤、铜线、无线电 | 网卡硬件 |

> **为什么要分层？** 分层使得每一层可以独立演进，只要接口不变。应用层不需要关心数据如何经过路由到达对方，传输层不需要关心数据是通过光纤还是WiFi传输。

**数据传输过程（封装与解封装）：**

```
发送方（封装）：
应用层数据 → 表示层加密 → 会话层添加会话ID → 传输层加TCP头 → 网络层加IP头 → 数据链路层加帧头帧尾 → 物理层比特流

接收方（解封装）：
物理层比特流 → 数据链路层解析帧 → 网络层解析IP → 传输层解析TCP → 会话层核对会话 → 表示层解密 → 应用层拿到数据
```

### 11.1.2 TCP/IP 协议栈

TCP/IP 是实际广泛使用的网络协议族，相比 OSI 更简洁，只有四层（或五层实际实现）：

| TCP/IP 层 | 对应 OSI | 主要协议 | 核心职责 |
|-----------|---------|---------|---------|
| 应用层 | 5-7 层 | HTTP、HTTPS、FTP、DNS、SMTP | 应用程序间数据交换 |
| 传输层 | 4 层 | **TCP**、**UDP** | 进程间端到端通信 |
| 网络层 | 3 层 | **IP**、ICMP、ARP、RARP | 主机间寻址与路由 |
| 链路层 | 1-2 层 | Ethernet、PPP、Wi-Fi | 相邻节点帧传输 |

**TCP/IP 四层数据传输示意：**

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   应用层      │ →  │   传输层      │ →  │   网络层      │ →  │  链路层       │
│  (HTTP/Data) │    │ (TCP Segment)│    │  (IP Packet) │    │  (Eth Frame) │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### 11.1.3 协议与端口号

端口号（Port）是传输层用来区分同一台主机上不同进程的标识，范围 0-65535：

| 端口范围 | 用途 | 常见服务 |
|---------|------|---------|
| 0-1023 | 知名端口（系统保留） | HTTP(80)、HTTPS(443)、SSH(22)、MySQL(3306) |
| 1024-49151 | 注册端口 | Tomcat(8080)、Redis(6379)、MongoDB(27017) |
| 49152-65535 | 动态/私有端口 | 客户端临时端口 |

**常见服务端口速查：**

| 端口 | 服务 | 说明 |
|------|------|------|
| 21 | FTP | 文件传输（明文） |
| 22 | SSH | 安全远程登录 |
| 23 | Telnet | 远程登录（明文，不安全） |
| 25 | SMTP | 邮件发送 |
| 53 | DNS | 域名解析（TCP/UDP） |
| 80 | HTTP | 万维网（明文） |
| 110 | POP3 | 邮件收取 |
| 443 | HTTPS | HTTP + SSL/TLS（加密） |
| 3306 | MySQL | 数据库 |
| 6379 | Redis | 缓存 |
| 8080 | HTTP Alt | 常见 Web 服务备用端口 |

### 11.1.4 Java 网络编程 API 概述

Java 的网络编程能力主要由 `java.net` 和 `java.nio.channels` 提供：

| 类/包 | 作用 | 层级 |
|-------|------|------|
| `InetAddress` | 表示 IP 地址 | 网络层 |
| `InetSocketAddress` | IP + 端口组合 | 传输层 |
| `URL` | 统一资源定位符 | 应用层 |
| `URLConnection` | URL 连接抽象 | 应用层 |
| `HttpURLConnection` | HTTP 连接 | 应用层 |
| `ServerSocket` | TCP 服务端监听 | 传输层 |
| `Socket` | TCP 客户端/服务端通信 | 传输层 |
| `DatagramSocket` | UDP 发送/接收 | 传输层 |
| `DatagramPacket` | UDP 数据报 | 传输层 |
| `ServerSocketChannel` | NIO TCP 服务端 | 传输层 |
| `SocketChannel` | NIO TCP 客户端 | 传输层 |
| `DatagramChannel` | NIO UDP | 传输层 |
| `Selector` | 多路复用选择器 | 传输层 |

---

## 11.2 TCP 协议详解

### 11.2.1 TCP 的核心特性

**TCP（Transmission Control Protocol）** 是面向连接的、可靠的、基于字节流的传输层协议。相比 UDP，TCP 提供：

| 特性 | 说明 |
|------|------|
| **面向连接** | 传输前必须建立连接（类似打电话），传输后释放连接 |
| **可靠传输** | ACK 确认、超时重传、序列号校验，保证数据不丢失、不重复 |
| **字节流服务** | 无消息边界，应用程序需自行处理消息边界问题 |
| **全双工** | 双方可同时发送和接收数据 |
| **拥塞控制** | 慢启动、拥塞避免、快速恢复等算法保护网络 |

### 11.2.2 TCP 三次握手（建立连接）

**三次握手是 TCP 建立连接的过程，目的是同步双方的序列号，确认双方的接收能力。**

```
客户端                                      服务端
   │                                          │
   │ ──────── SYN (seq=x, SYN=1) ──────────→  │  第一次握手：客户端发送SYN，请求建立连接
   │                                          │
   │  ←──── SYN+ACK (seq=y, ack=x+1, SYN=1, ACK=1) ─── │  第二次握手：服务端发送SYN+ACK
   │                                          │
   │ ──────── ACK (seq=x+1, ack=y+1, ACK=1) ─→ │  第三次握手：客户端发送ACK，连接建立
   │                                          │
   │         [双方可以传输数据]                │
```

**三次握手状态分析：**

| 握手 | 客户端状态 | 服务端状态 | 关键字段 |
|------|-----------|-----------|---------|
| 第一次握手 | `SYN_SENT` | `LISTEN` | SYN=1, seq=x |
| 第二次握手 | `SYN_SENT` | `SYN_RCVD` | SYN=1, ACK=1, seq=y, ack=x+1 |
| 第三次握手 | `ESTABLISHED` | `SYN_RCVD` → `ESTABLISHED` | ACK=1, seq=x+1, ack=y+1 |

**为什么是三次？**

- 第一次握手：服务端确认"客户端的发送能力 + 服务端的接收能力 OK"
- 第二次握手：客户端确认"服务端的发送能力 + 客户端的接收能力 OK"（同时服务端也知道客户端能收了）
- 第三次握手：服务端确认"客户端的接收能力 OK"（此时双方都确认了彼此的双向通信能力）

> **坑点**：如果只两次握手，服务端无法确认客户端是否收到了自己的 SYN+ACK，可能导致服务端空等永不存在的 ACK，浪费资源。三次是双方都能确认对方接收能力的最小次数。

**Java 代码模拟三次握手（简化）：**

```java
public class TCPHandshakeDemo {
    public static void main(String[] args) throws Exception {
        // 使用 netstat 观察三次握手
        // 启动一个 TCP 服务端
        ServerSocket server = new ServerSocket(9999);
        System.out.println("服务端监听端口 9999...");

        // 启动一个客户端连接
        new Thread(() -> {
            try {
                Thread.sleep(1000); // 等待服务端启动
                Socket socket = new Socket("127.0.0.1", 9999);
                System.out.println("客户端已连接！");
                socket.close();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();

        Socket client = server.accept();
        System.out.println("服务端收到客户端连接！");
        client.close();
        server.close();
    }
}
```

在另一个终端执行 `netstat -an | grep 9999`，可以看到 TCP 连接状态变化：`LISTEN` → `SYN_RCVD` → `ESTABLISHED`。

### 11.2.3 TCP 四次挥手（断开连接）

**四次挥手是 TCP 断开连接的过程，由于是全双工通信，每个方向都需要单独关闭。**

```
客户端                                      服务端
   │                                          │
   │ ──────── FIN (seq=u, FIN=1) ──────────→  │  第一次挥手：客户端请求断开（不再发送数据）
   │                                          │
   │  ←─────── ACK (ack=u+1, ACK=1) ──────── │  第二次挥手：服务端确认（可能还有数据要发）
   │                                          │
   │     [客户端等待服务端的数据和FIN]          │
   │                                          │
   │  ←─────── FIN (seq=w, FIN=1) ────────── │  第三次挥手：服务端发完数据，请求断开
   │                                          │
   │ ──────── ACK (ack=w+1, ACK=1) ────────→ │  第四次挥手：客户端确认，2MSL后关闭
   │                                          │
   │   [客户端等待 2MSL 后彻底关闭]            │
```

**四次挥手状态分析：**

| 挥手 | 客户端状态 | 服务端状态 | 关键字段 |
|------|-----------|-----------|---------|
| 第一次挥手 | `FIN_WAIT_1` | `ESTABLISHED` | FIN=1, seq=u |
| 第二次挥手 | `FIN_WAIT_2` | `CLOSE_WAIT` | ACK=1, ack=u+1 |
| 第三次挥手 | `TIME_WAIT` | `LAST_ACK` | FIN=1, seq=w |
| 第四次挥手 | `TIME_WAIT` → `CLOSED` | `CLOSED` | ACK=1, ack=w+1 |

**为什么需要 2MSL 的 TIME_WAIT？**

1. **确保最后的 ACK 能到达**：如果第四次挥手的 ACK 丢失，服务端会重发 FIN，客户端需要在 TIME_WAIT 内处理重发的 FIN
2. **让本连接的残留报文在网络中消散**：防止新连接的相同四元组被旧报文干扰

> **MSL（Maximum Segment Lifetime）** 是报文最大生存时间，通常为 30 秒或 60 秒，2MSL = 60~120 秒。

**Java 观察 TIME_WAIT：**

```java
// 高并发服务器中，频繁创建销毁 Socket 会积累大量 TIME_WAIT 状态的连接
// 可通过设置 socket 选项缓解
ServerSocket server = new ServerSocket(8080);
server.setReuseAddress(true); // 允许地址复用，缓解 TIME_WAIT 问题

Socket socket = server.accept();
System.out.println("连接状态: " + socket.isConnected());
socket.close();
server.close();
```

### 11.2.4 TCP 状态流转图

以下是完整的 TCP 状态机：

```
                    ┌─────────┐
         主动打开   │  CLOSED │
         (客户端)    └────┬────┘
                    SYN_SENT │
                    (发送SYN) │
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    │  收SYN+ACK        │  收SYN             │  收SYN
    │  发送ACK           │  发送SYN+ACK       │  发送RST
    │                    │                    │
    ▼                    ▼                    │
ESTABLISHED ◀─────── SYN_RCVD ◀──────── LISTEN
    │                    │                    │
    │  发送FIN           │  收ACK             │
    │  进入FIN_WAIT_1   │  进入ESTABLISHED   │
    │                    │                    │
    │  收ACK             │                    │
    │  进入FIN_WAIT_2   │                    │
    │                    │                    │
    │  收FIN            │                    │
    │  发送ACK           │                    │
    │  进入TIME_WAIT    │                    │
    │  2MSL后→CLOSED   │                    │
    └──────────────────────────────────────────┘
```

**常见状态及其含义：**

| 状态 | 含义 | 常见场景 |
|------|------|---------|
| `LISTEN` | 服务端监听中，等待连接 | `ServerSocket` 启动 |
| `SYN_SENT` | 客户端已发送 SYN | 客户端调用 `connect()` |
| `SYN_RCVD` | 收到对方的 SYN 并回复了 SYN+ACK | 三次握手中间状态 |
| `ESTABLISHED` | 连接已建立，双方可正常通信 | 正常通信状态 |
| `FIN_WAIT_1` | 已发送 FIN，等待对方 ACK | 主动关闭，第一次挥手 |
| `FIN_WAIT_2` | 收到 ACK，等待对方 FIN | 主动关闭，第二次挥手后 |
| `TIME_WAIT` | 等待 2MSL 后关闭 | 主动关闭，第四次挥手后 |
| `CLOSE_WAIT` | 收到 FIN，等待应用层关闭 | 被动关闭，第一次挥手后 |
| `LAST_ACK` | 已发送 FIN，等待对方 ACK | 被动关闭，第三次挥手后 |
| `CLOSED` | 连接关闭 | — |

### 11.2.5 TCP 状态与 Java Socket 的对应关系

```java
// Java 中观察 TCP 连接状态（通过 netstat / ss 命令）
// JVM 内部不直接暴露 TCP 状态，但可以通过以下方式间接观察

ServerSocket server = new ServerSocket(8080);
server.setReuseAddress(true); // 对应 Linux 的 SO_REUSEADDR

Socket client = server.accept();
// 此时服务端处于 ESTABLISHED
// 客户端（如果也调用了 close）可能处于 TIME_WAIT

System.out.println("服务端: " + client.getLocalAddress() + ":" + client.getLocalPort());
System.out.println("客户端: " + client.getInetAddress() + ":" + client.getPort());
```

> **坑点**：在高并发短连接场景下，`TIME_WAIT` 堆积会耗尽可用端口。解决方案：`server.setReuseAddress(true)`、启用 `SO_REUSEADDR`，或调整内核参数 `net.ipv4.tcp_tw_reuse=1`。

---

## 11.3 HTTP/HTTPS 协议

### 11.3.1 HTTP 协议基础

**HTTP（HyperText Transfer Protocol）** 是应用层协议，是 Web 的基础。HTTP/1.1 是目前最主流的版本，HTTP/2 和 HTTP/3 逐步普及。

**HTTP 请求结构：**

```
请求行    GET /index.html HTTP/1.1\r\n
请求头    Host: www.example.com\r\n
          User-Agent: Java/11\r\n
          Accept: text/html\r\n
          \r\n          (空行，分隔 header 和 body)
请求体    (可选，POST/PUT时有) name=value&age=25
```

**请求方法：**

| 方法 | 语义 | 幂等 | 有Body | 常见场景 |
|------|------|------|-------|---------|
| GET | 获取资源 | ✅ | ❌ | 查询、加载页面 |
| POST | 提交数据 | ❌ | ✅ | 表单提交、登录 |
| PUT | 更新资源（完整） | ✅ | ✅ | 更新全部字段 |
| DELETE | 删除资源 | ✅ | ❌ | 删除数据 |
| PATCH | 部分更新 | ❌ | ✅ | 更新部分字段 |
| HEAD | 获取头部（无Body） | ✅ | ❌ | 检查资源是否存在 |
| OPTIONS | 查询支持的方法 | ✅ | ❌ | CORS 预检 |

**HTTP 响应结构：**

```
状态行    HTTP/1.1 200 OK\r\n
响应头    Content-Type: text/html; charset=UTF-8\r\n
          Content-Length: 1234\r\n
          Server: Apache\r\n
          \r\n          (空行)
响应体    <html>...</html>
```

**常见状态码：**

| 状态码 | 含义 | 常见场景 |
|--------|------|---------|
| 200 | OK | 成功 |
| 201 | Created | 资源创建成功（POST 成功） |
| 204 | No Content | 成功但无返回体（DELETE 成功） |
| 301 | Moved Permanently | 永久重定向 |
| 302 | Found | 临时重定向 |
| 304 | Not Modified | 缓存未过期 |
| 400 | Bad Request | 请求格式错误 |
| 401 | Unauthorized | 未认证（需要登录） |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 405 | Method Not Allowed | 请求方法不支持 |
| 409 | Conflict | 资源冲突 |
| 422 | Unprocessable Entity | 参数校验失败 |
| 429 | Too Many Requests | 请求过于频繁 |
| 500 | Internal Server Error | 服务器内部错误 |
| 502 | Bad Gateway | 网关错误 |
| 503 | Service Unavailable | 服务不可用 |
| 504 | Gateway Timeout | 网关超时 |

### 11.3.2 Java 发送 HTTP 请求

**使用 HttpURLConnection：**

```java
import java.net.*;
import java.io.*;

public class HttpClientDemo {
    public static void main(String[] args) throws Exception {
        URL url = new URL("https://httpbin.org/get?name=Java&version=11");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();

        // 设置请求方法
        conn.setRequestMethod("GET");
        conn.setConnectTimeout(5000);    // 连接超时 5s
        conn.setReadTimeout(5000);       // 读取超时 5s
        conn.setRequestProperty("User-Agent", "Java-HttpClient/1.0");

        // 获取响应码
        int code = conn.getResponseCode();
        System.out.println("状态码: " + code);

        // 读取响应头
        Map<String, List<String>> headers = conn.getHeaderFields();
        headers.forEach((k, v) -> System.out.println(k + ": " + v));

        // 读取响应体
        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(conn.getInputStream(), "UTF-8"))) {
            String line;
            StringBuilder body = new StringBuilder();
            while ((line = br.readLine()) != null) {
                body.append(line).append("\n");
            }
            System.out.println("响应体:\n" + body);
        }

        conn.disconnect();
    }
}
```

**POST 请求带 JSON body：**

```java
public static String postJson(String urlStr, String json) throws Exception {
    URL url = new URL(urlStr);
    HttpURLConnection conn = (HttpURLConnection) url.openConnection();

    conn.setRequestMethod("POST");
    conn.setDoOutput(true);                          // 允许写Body
    conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
    conn.setConnectTimeout(5000);
    conn.setReadTimeout(5000);

    // 写入请求体
    try (OutputStream os = conn.getOutputStream()) {
        os.write(json.getBytes("UTF-8"));
    }

    // 读取响应
    int code = conn.getResponseCode();
    StringBuilder resp = new StringBuilder();
    try (BufferedReader br = new BufferedReader(
            new InputStreamReader(
                code >= 400 ? conn.getErrorStream() : conn.getInputStream(), "UTF-8"))) {
        String line;
        while ((line = br.readLine()) != null) {
            resp.append(line);
        }
    }
    return resp.toString();
}
```

### 11.3.3 HTTPS 与 SSL/TLS

**HTTPS = HTTP + TLS/SSL**，在 HTTP 和 TCP 之间加了一层 TLS（Transport Layer Security），对传输内容加密。

**TLS 工作原理：**

```
客户端                                          服务端
   │                                              │
   │  ─── ClientHello (支持的TLS版本、加密套件、随机数) ──→  │
   │                                              │
   │  ←── ServerHello (选定TLS版本、加密套件、服务端随机数) ─ │
   │  ←── Certificate (服务端证书，包含公钥) ─────────────── │
   │  ←── ServerHelloDone ──────────────────────  │
   │                                              │
   │  验证证书（检查颁发者、有效期、域名等）           │
   │                                              │
   │  ─── ClientKeyExchange (用服务端公钥加密的PreMasterSecret) ──→ │
   │  ─── ChangeCipherSpec (此后用协商的密钥加密) ──→  │
   │  ─── Finished (加密的握手消息摘要) ───────────→  │
   │                                              │
   │  ←── ChangeCipherSpec ────────────────────  │
   │  ←── Finished ───────────────────────────  │
   │                                              │
   │         [对称加密通信开始]                    │
```

**Java 中使用 HTTPS（TrustAll 问题——仅限开发环境）：**

```java
// ⚠️ 这是开发/调试用代码，生产环境绝对不要这样写！
public static void disableCertificateValidation() throws Exception {
    // 创建不验证证书的 TrustManager（危险，仅调试用）
    TrustManager[] trustAll = new TrustManager[]{
        new X509TrustManager() {
            public X509Certificate[] getAcceptedIssuers() { return null; }
            public void checkClientTrusted(X509Certificate[] certs, String t) {}
            public void checkServerTrusted(X509Certificate[] certs, String t) {}
        }
    };

    SSLContext sc = SSLContext.getInstance("TLS");
    sc.init(null, trustAll, new java.security.SecureRandom());

    // 全局设置为不验证（⚠️ 不要在生产环境使用）
    HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory());
    HttpsURLConnection.setDefaultHostnameVerifier((h, s) -> true);
}
```

**正确的 HTTPS 证书验证（生产环境）：**

```java
// 生产环境应该加载真实的 CA 证书
public static void properHttpsRequest() throws Exception {
    // 方法1：使用系统默认的证书库（推荐，大多数情况够用）
    // Java 默认使用 $JAVA_HOME/lib/security/cacerts 作为信任库

    URL url = new URL("https://api.example.com/data");
    HttpsURLConnection conn = (HttpsURLConnection) url.openConnection();
    conn.setRequestMethod("GET");
    // 默认就使用系统信任库，无需额外配置
    int code = conn.getResponseCode();
    System.out.println("HTTPS 请求成功，状态码: " + code);
}
```

### 11.3.4 HTTP 缓存机制

HTTP 缓存通过响应头控制，是提升性能的关键：

| 响应头 | 作用 | 示例 |
|--------|------|------|
| `Cache-Control` | 缓存控制策略 | `max-age=3600`, `no-cache`, `no-store`, `private`, `public` |
| `Expires` | 缓存过期绝对时间 | `Expires: Wed, 21 Oct 2025 07:28:00 GMT` |
| `Last-Modified` | 资源最后修改时间 | `Last-Modified: Wed, 21 Oct 2025 07:28:00 GMT` |
| `ETag` | 资源版本标识（哈希） | `ETag: "33a64df551425fcc55e4d42a148795d9"` |
| `If-Modified-Since` | 请求时携带，询问资源是否变化 | 配合 `Last-Modified` |
| `If-None-Match` | 请求时携带，询问资源是否变化 | 配合 `ETag` |

**缓存流程：**

```
浏览器请求 → 检查本地缓存 → 有且未过期 → 直接使用（200 from cache）
                         → 已过期 → 发送条件请求(If-None-Match/If-Modified-Since)
                                        → 304 Not Modified → 使用缓存
                                        → 200 OK → 返回新资源，更新缓存
           → 无缓存 → 发送完整请求 → 200 OK → 存储缓存
```

### 11.3.5 HTTP/2 与 HTTP/3 简介

**HTTP/2 主要改进：**

- **多路复用（Multiplexing）**：一个 TCP 连接上并行多个请求/响应帧，不需排队（解决 HTTP/1.1 队头阻塞）
- **Header 压缩**：使用 HPACK 算法压缩请求头（HTTP/1.1 每次请求都带重复的 header）
- **Server Push**：服务端主动推送资源（如 HTML 引用了 CSS，服务端主动推送 CSS）
- **二进制分帧**：取代明文文本，帧是最小传输单位

**HTTP/3 主要改进：**

- 基于 **QUIC** 协议（UDP 实现），解决 TCP 队头阻塞问题
- 0-RTT 或 1-RTT 建立连接（更快）
- 内置 TLS 1.3

> Java 11+ 原生不支持 HTTP/2 客户端，需使用 Apache HttpClient 或 OkHttp。Java 17+ 可以通过 `--add-modules jdk.incubator.http2` 启用 HTTP/2 支持。

---

## 11.4 Socket 编程

### 11.4.1 TCP Socket 编程

**Socket 是对 TCP 连接两端的抽象，Java 中通过 `ServerSocket`（服务端）和 `Socket`（客户端）实现。**

#### 11.4.1.1 TCP 服务端

```java
public class TcpServer {
    public static void main(String[] args) throws Exception {
        // 1. 创建服务端 ServerSocket，监听端口
        ServerSocket server = new ServerSocket(8888);
        System.out.println("服务端启动，监听端口 8888...");

        // 2. 循环接受客户端连接（这里是单线程版，生产环境应用线程池）
        while (true) {
            Socket clientSocket = server.accept(); // 阻塞，直到有客户端连接
            System.out.println("收到客户端连接: " + clientSocket.getRemoteSocketAddress());

            // 3. 处理客户端请求（这里用线程池处理，避免阻塞主循环）
            handleClient(clientSocket);
        }
    }

    private static void handleClient(Socket socket) {
        ExecutorService pool = Executors.newFixedThreadPool(4);
        pool.submit(() -> {
            try {
                // 获取输入流（读客户端发来的数据）
                BufferedReader reader = new BufferedReader(
                        new InputStreamReader(socket.getInputStream(), "UTF-8"));

                // 获取输出流（向客户端发数据）
                PrintWriter writer = new PrintWriter(
                        new OutputStreamWriter(socket.getOutputStream(), "UTF-8"), true);

                String request;
                while ((request = reader.readLine()) != null) {
                    System.out.println("收到: " + request);
                    // Echo 响应
                    writer.println("服务端收到: " + request);
                }
            } catch (IOException e) {
                System.err.println("客户端处理异常: " + e.getMessage());
            } finally {
                try { socket.close(); } catch (IOException e) {}
            }
        });
    }
}
```

#### 11.4.1.2 TCP 客户端

```java
public class TcpClient {
    public static void main(String[] args) throws Exception {
        // 1. 创建 Socket，指定服务端地址和端口
        try (Socket socket = new Socket("127.0.0.1", 8888)) {
            // 2. 获取输出流，发送数据
            PrintWriter writer = new PrintWriter(
                    new OutputStreamWriter(socket.getOutputStream(), "UTF-8"), true);

            // 3. 获取输入流，接收响应
            BufferedReader reader = new BufferedReader(
                    new InputStreamReader(socket.getInputStream(), "UTF-8"));

            // 4. 发送请求
            writer.println("Hello Server!");
            System.out.println("服务端响应: " + reader.readLine());

            // 5. 发送多条消息
            writer.println("第二条消息");
            writer.println("第三条消息");
            System.out.println("服务端响应: " + reader.readLine());
        } // try-with-resources 自动关闭 socket
    }
}
```

#### 11.4.1.3 服务端多线程版本（线程池）

```java
public class MultiThreadedTcpServer {
    private static final int PORT = 8888;
    private static final int THREAD_POOL_SIZE = 10;

    public static void main(String[] args) throws Exception {
        ServerSocket server = new ServerSocket(PORT);
        System.out.println("多线程 TCP 服务端启动，端口: " + PORT);

        ExecutorService pool = Executors.newFixedThreadPool(THREAD_POOL_SIZE);

        while (true) {
            Socket clientSocket = server.accept(); // 阻塞等待
            pool.submit(() -> handleClient(clientSocket));
        }
    }

    private static void handleClient(Socket socket) {
        String clientInfo = socket.getRemoteSocketAddress().toString();
        System.out.println("新连接: " + clientInfo);

        try (socket) {
            BufferedReader reader = new BufferedReader(
                    new InputStreamReader(socket.getInputStream(), "UTF-8"));
            PrintWriter writer = new PrintWriter(
                    new OutputStreamWriter(socket.getOutputStream(), "UTF-8"), true);

            String request;
            while ((request = reader.readLine()) != null) {
                System.out.println("[" + clientInfo + "] " + request);
                if ("exit".equalsIgnoreCase(request)) {
                    writer.println("bye!");
                    break;
                }
                writer.println("Echo: " + request);
            }
        } catch (IOException e) {
            System.err.println("客户端异常: " + e.getMessage());
        }
        System.out.println("连接关闭: " + clientInfo);
    }
}
```

#### 11.4.1.4 Socket 选项

```java
ServerSocket server = new ServerSocket(8080);

// 常用 ServerSocket 选项
server.setReuseAddress(true);          // SO_REUSEADDR，允许端口复用（TIME_WAIT期间可重启）
server.setSoTimeout(0);                // SO_TIMEOUT，accept 超时（0 表示无限等待）
server.setReceiveBufferSize(1024 * 64); // SO_RCVBUF，接收缓冲区大小

Socket client = server.accept();

// 常用 Socket 选项
client.setTcpNoDelay(true);            // TCP_NODELAY，禁用 Nagle 算法，小数据包立即发送
client.setSoLinger(true, 30);          // SO_LINGER，close 时等待数据发送完成
client.setKeepAlive(true);             // SO_KEEPALIVE，开启 TCP 保活
client.setSendBufferSize(1024 * 64);   // SO_SNDBUF，发送缓冲区大小
client.setReceiveBufferSize(1024 * 64);// SO_RCVBUF，接收缓冲区大小
```

### 11.4.2 UDP Socket 编程

**UDP（User Datagram Protocol）是无连接的、不可靠的、面向数据报的传输层协议。不需要建立连接，发送_datagram_，不保证交付。**

#### 11.4.2.1 UDP 服务端

```java
public class UdpServer {
    public static void main(String[] args) throws Exception {
        // 1. 创建 DatagramSocket，指定监听端口
        DatagramSocket socket = new DatagramSocket(8888);
        System.out.println("UDP 服务端启动，监听端口 8888...");

        byte[] buffer = new byte[1024];

        while (true) {
            // 2. 创建接收数据包（包含数据和发送方地址）
            DatagramPacket packet = new DatagramPacket(buffer, buffer.length);

            // 3. 阻塞接收数据
            socket.receive(packet); // 阻塞直到收到数据
            String msg = new String(packet.getData(), 0, packet.getLength(), "UTF-8");
            System.out.println("收到客户端消息: " + msg);
            System.out.println("发送方: " + packet.getAddress() + ":" + packet.getPort());

            // 4. 响应数据给客户端
            String response = "服务端收到: " + msg;
            DatagramPacket resp = new DatagramPacket(
                    response.getBytes("UTF-8"),
                    response.getBytes().length,
                    packet.getAddress(),
                    packet.getPort()
            );
            socket.send(resp);
        }
    }
}
```

#### 11.4.2.2 UDP 客户端

```java
public class UdpClient {
    public static void main(String[] args) throws Exception {
        // 1. 创建 DatagramSocket（不指定端口，由系统分配临时端口）
        try (DatagramSocket socket = new DatagramSocket()) {
            // 2. 服务端地址
            InetAddress serverAddr = InetAddress.getByName("127.0.0.1");
            int serverPort = 8888;

            // 3. 发送数据
            String msg = "Hello UDP Server!";
            DatagramPacket packet = new DatagramPacket(
                    msg.getBytes("UTF-8"),
                    msg.getBytes().length,
                    serverAddr,
                    serverPort
            );
            socket.send(packet);
            System.out.println("已发送: " + msg);

            // 4. 接收响应
            byte[] buffer = new byte[1024];
            DatagramPacket resp = new DatagramPacket(buffer, buffer.length);
            socket.receive(resp); // 阻塞等待响应
            String response = new String(resp.getData(), 0, resp.getLength(), "UTF-8");
            System.out.println("收到服务端响应: " + response);
        }
    }
}
```

#### 11.4.2.3 TCP vs UDP 对比

| 对比项 | TCP | UDP |
|--------|-----|-----|
| 连接性 | 面向连接（三次握手） | 无连接（直接发送数据报） |
| 可靠性 | 可靠（ACK、重传、序列号） | 不可靠（不保证交付） |
| 传输单位 | 字节流（无消息边界） | 数据报（DatagramPacket，有边界） |
| 速度 | 相对较慢（建立连接、拥塞控制） | 较快（无连接开销，无拥塞控制） |
| 适用场景 | 文件传输、网页、邮件、远程登录 | DNS 查询、视频流、实时游戏、语音通话 |
| 头部大小 | 20-60 字节 | 8 字节（固定） |

### 11.4.3 URL 与 URLConnection

#### 11.4.3.1 URL 解析

```java
public class UrlParseDemo {
    public static void main(String[] args) throws Exception {
        URL url = new URL("https://username:password@example.com:8080/path?query=value#anchor");

        System.out.println("协议:   " + url.getProtocol());    // https
        System.out.println("主机:   " + url.getHost());        // example.com
        System.out.println("端口:   " + url.getPort());        // 8080（-1 表示使用默认端口）
        System.out.println("路径:   " + url.getPath());        // /path
        System.out.println("查询:   " + url.getQuery());       // query=value
        System.out.println("锚点:   " + url.getRef());         // anchor
        System.out.println("用户信息:" + url.getUserInfo());   // username:password
    }
}
```

#### 11.4.3.2 URLConnection 的使用

```java
public class UrlConnectionDemo {
    public static void main(String[] args) throws Exception {
        URL url = new URL("https://httpbin.org/get");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();

        conn.setRequestMethod("GET");
        conn.setConnectTimeout(5000);
        conn.setReadTimeout(5000);

        // 打印所有响应头
        conn.getHeaderFields().forEach((k, v) -> {
            System.out.println(k + " = " + v);
        });

        // 读取响应体
        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(conn.getInputStream()))) {
            br.lines().forEach(System.out::println);
        }
    }
}
```

### 11.4.4 常见 Socket 编程坑点

**坑点1：流没有关闭导致资源泄漏**

```java
// ❌ 错误：流没有关闭
Socket socket = new Socket("127.0.0.1", 8888);
PrintWriter writer = new PrintWriter(socket.getOutputStream());
// 如果这里抛异常，下面的 close 不会执行，socket 资源泄漏

// ✅ 正确：使用 try-with-resources
try (Socket socket = new Socket("127.0.0.1", 8888);
     PrintWriter writer = new PrintWriter(socket.getOutputStream());
     BufferedReader reader = new BufferedReader(
             new InputStreamReader(socket.getInputStream()))) {
    writer.println("hello");
    String resp = reader.readLine();
    System.out.println(resp);
} // 自动关闭所有资源
```

**坑点2：TCP 字节流没有消息边界**

```java
// ❌ 错误：假设一次 readLine 就是一条消息
// TCP 是字节流，不保证一次 read() 对应一次 write()
// 如果发送 "Hello" 和 "World" 两次，可能被合并成一个包
writer.println("Hello");
writer.println("World");
// 接收方 readLine() 可能一次性读到 "Hello\r\nWorld\r\n"

✅ 正确做法：
// 方法1：自定义协议（长度前缀）
// 发送：[4字节长度][数据]
// 接收：先读4字节得到长度，再读指定长度数据

// 方法2：使用分隔符（不适合二进制数据）
// 发送：每条消息以 \n 结尾，接收方按行读取（二进制数据含\n会误判）

// 方法3：使用消息框架（Netty 等）自动处理粘包半包
```

**坑点3：服务端单线程阻塞导致无法响应其他客户端**

```java
// ❌ 错误：串行处理，一个客户端处理慢会阻塞所有其他客户端
while (true) {
    Socket client = server.accept();
    // 如果这里处理很慢，新客户端只能等待
    handleClient(client); // 阻塞调用
}

// ✅ 正确：每连接一个线程处理
ExecutorService pool = Executors.newCachedThreadPool();
while (true) {
    Socket client = server.accept();
    pool.submit(() -> handleClient(client)); // 非阻塞
}
```

**坑点4：UDP 数据报丢失和乱序没有处理**

```java
// UDP 不保证交付，以下情况应用层必须自行处理：
// 1. 数据包丢失 → 需要超时重传
// 2. 数据包乱序 → 需要序列号
// 3. 数据包重复 → 需要去重

// 简单的心跳机制示例
public class UdpHeartbeat {
    private static final int TIMEOUT = 3000; // 3秒超时
    private static final int RETRY = 3;

    public static boolean sendWithRetry(DatagramSocket socket,
                                         InetAddress addr, int port, String msg) {
        for (int i = 0; i < RETRY; i++) {
            try {
                DatagramPacket p = new DatagramPacket(
                        msg.getBytes(), msg.length(), addr, port);
                socket.send(p);

                byte[] buf = new byte[1024];
                DatagramPacket resp = new DatagramPacket(buf, buf.length);
                socket.receive(resp); // 阻塞，有响应即成功

                return true;
            } catch (SocketTimeoutException e) {
                System.out.println("第 " + (i + 1) + " 次超时，重试...");
            } catch (IOException e) {
                return false;
            }
        }
        return false;
    }
}
```

---

## 11.5 NIO 与网络编程

### 11.5.1 NIO 概述

Java NIO（New I/O，非阻塞 I/O，JDK 1.4+）引入了三个核心概念：**Channel（通道）**、**Buffer（缓冲区）** 和 **Selector（选择器）**，实现了 I/O 多路复用，使单个线程能处理多个并发连接。

**NIO vs 传统 I/O 对比：**

| 对比项 | 传统 I/O（阻塞） | NIO（非阻塞 + 多路复用） |
|--------|----------------|------------------------|
| 编程模型 | 每连接一个线程，或线程池 | 单线程处理多个连接 |
| 核心 API | Stream、Reader/Writer | Channel、Buffer、Selector |
| I/O 模式 | 阻塞（read/write 一直等到完成） | 非阻塞（立即返回，无数据时返回 null） |
| 消息边界 | 由 Stream 隐式处理 | 需要自行处理（通过协议设计） |
| 适用场景 | 低并发、简单场景 | 高并发（C10K、C100K 问题） |

### 11.5.2 Buffer（缓冲区）

**Buffer 是 NIO 的核心，用于读写数据。本质是一个数组，加上四个指针（position、limit、capacity、mark）。**

#### 11.5.2.1 Buffer 的四个核心属性

```java
/*
Buffer 内部结构：
┌─────────────────────────────┐
│  capacity（容量）            │  缓冲区数组大小，创建时固定
├─────────────────────────────┤
│  limit（限制）               │  第一个不能读/写的元素的索引
├─────────────────────────────┤
│  position（位置）            │  当前读/写位置的索引
├─────────────────────────────┤
│  [mark]                     │  书签，可记录某个 position
└─────────────────────────────┘
*/

public class BufferDemo {
    public static void main(String[] args) {
        // 创建一个容量为 10 的 ByteBuffer
        ByteBuffer buffer = ByteBuffer.allocate(10);
        System.out.println("初始状态:");
        System.out.println("  capacity=" + buffer.capacity());
        System.out.println("  limit=" + buffer.limit());
        System.out.println("  position=" + buffer.position());
        System.out.println("  remaining=" + buffer.remaining());

        // 写入数据
        buffer.put((byte) 1);
        buffer.put((byte) 2);
        buffer.put((byte) 3);
        System.out.println("\n写入3个字节后:");
        System.out.println("  position=" + buffer.position()); // 3

        // 切换为读模式（flip 将 limit 设置为 position，position 归零）
        buffer.flip();
        System.out.println("\nflip() 后:");
        System.out.println("  position=" + buffer.position()); // 0
        System.out.println("  limit=" + buffer.limit());       // 3

        // 读取数据
        System.out.println("\n读取数据:");
        while (buffer.hasRemaining()) {
            System.out.print(buffer.get() + " "); // 1 2 3
        }

        // 清除缓冲区（position=0, limit=capacity，数据不清除）
        buffer.clear();
        System.out.println("\n\nclear() 后:");
        System.out.println("  position=" + buffer.position()); // 0
        System.out.println("  limit=" + buffer.limit());       // 10
    }
}
```

#### 11.5.2.2 Buffer 的类型

| Buffer 类型 | 对应数据类型 | 说明 |
|------------|-------------|------|
| `ByteBuffer` | byte | 最常用，通过 `allocate()`（堆内）或 `allocateDirect()`（堆外）创建 |
| `CharBuffer` | char | 字符缓冲区 |
| `ShortBuffer` | short | 短整型 |
| `IntBuffer` | int | 整型 |
| `LongBuffer` | long | 长整型 |
| `FloatBuffer` | float | 浮点型 |
| `DoubleBuffer` | double | 双精度浮点型 |
| `MappedByteBuffer` | byte | 文件内存映射（`FileChannel.map()`） |

#### 11.5.2.3 直接缓冲区 vs 堆缓冲区

```java
// 堆缓冲区（HeapByteBuffer）：JVM 堆内，速度快，但读写需要拷贝到直接缓冲区
ByteBuffer heapBuffer = ByteBuffer.allocate(1024);

// 直接缓冲区（DirectByteBuffer）：堆外内存，不受 GC 管理，减少一次内存拷贝
// 适合高吞吐场景（网络发送、文件读写）
ByteBuffer directBuffer = ByteBuffer.allocateDirect(1024);

// 注意：直接缓冲区创建和销毁成本更高，适合长期使用的场景
```

#### 11.5.2.4 Buffer 的高级操作

```java
public class BufferAdvancedDemo {
    public static void main(String[] args) {
        ByteBuffer buffer = ByteBuffer.allocate(20);

        // 批量写入
        byte[] data = "Hello, NIO!".getBytes();
        buffer.put(data);

        // compact()：将未读部分压缩到前面，继续写入
        buffer.flip();         // position=0, limit=12
        buffer.get(new byte[5]); // 读5个字节，position=5
        buffer.compact();      // 将 position=5 开始的7个字节移到前面，position=7, limit=20

        // rewind()：重读已读内容（position 归零，limit 不变）
        buffer.rewind();

        // mark() / reset()：书签功能
        buffer.mark();
        buffer.get();
        buffer.reset(); // position 回到 mark 处

        // duplicate()：创建视角不同的 Buffer（共享底层数组）
        ByteBuffer view = buffer.duplicate();

        // slice()：创建子缓冲区（从 position 到 limit 的视图）
        ByteBuffer slice = buffer.slice();
    }
}
```

### 11.5.3 Channel（通道）

**Channel 是对 I/O 操作的抽象，类似于流，但可以异步、非阻塞地操作。Channel 是双向的（可读可写），流是单向的。**

#### 11.5.3.1 核心 Channel 类型

| Channel | 说明 |
|---------|------|
| `FileChannel` | 文件 I/O，只能阻塞式操作 |
| `SocketChannel` | TCP 客户端/服务端 I/O，支持非阻塞模式 |
| `ServerSocketChannel` | TCP 服务端监听，支持非阻塞模式 |
| `DatagramChannel` | UDP I/O，支持非阻塞模式 |

#### 11.5.3.2 FileChannel 的使用

```java
public class FileChannelDemo {
    public static void main(String[] args) throws Exception {
        RandomAccessFile file = new RandomAccessFile("test.txt", "rw");
        FileChannel channel = file.getChannel();

        // 写入数据
        ByteBuffer writeBuf = ByteBuffer.allocate(1024);
        writeBuf.put("Hello FileChannel!".getBytes());
        writeBuf.flip(); // 切换读模式
        channel.write(writeBuf);

        // 读取数据
        ByteBuffer readBuf = ByteBuffer.allocate(1024);
        channel.read(readBuf);
        readBuf.flip();
        System.out.println("读取内容: " + new String(readBuf.array(), 0, readBuf.limit()));

        // 文件锁定（共享锁或排他锁）
        FileLock lock = channel.lock(); // 排他锁
        // FileLock lock = channel.lock(0, Long.MAX_VALUE, true); // 共享锁（需操作系统支持）
        System.out.println("文件锁定: " + lock.isValid());

        // 强制刷新到磁盘
        channel.force(true);

        lock.release();
        channel.close();
        file.close();
    }
}
```

#### 11.5.3.3 SocketChannel（TCP 客户端）

```java
public class NioTcpClient {
    public static void main(String[] args) throws Exception {
        // 1. 打开 SocketChannel
        SocketChannel channel = SocketChannel.open();
        channel.configureBlocking(false); // 设置非阻塞模式

        // 2. 连接服务端（非阻塞模式下，connect 是异步的）
        boolean connected = channel.connect(new InetSocketAddress("127.0.0.1", 8888));

        // 如果是阻塞模式，直接等待连接
        // channel.connect(...); // 阻塞直到连接建立

        if (!connected) {
            // 非阻塞模式下，等待连接完成
            while (!channel.finishConnect()) {
                System.out.println("连接中...");
                Thread.sleep(100);
            }
        }

        System.out.println("连接成功: " + channel.getRemoteAddress());

        // 3. 发送数据
        ByteBuffer buffer = ByteBuffer.allocate(1024);
        buffer.put("Hello NIO Server!".getBytes("UTF-8"));
        buffer.flip();
        channel.write(buffer);

        // 4. 接收数据
        buffer.clear();
        int read = channel.read(buffer);
        if (read > 0) {
            buffer.flip();
            byte[] data = new byte[buffer.remaining()];
            buffer.get(data);
            System.out.println("收到: " + new String(data, "UTF-8"));
        }

        // 5. 关闭
        channel.close();
    }
}
```

#### 11.5.3.4 ServerSocketChannel（TCP 服务端）

```java
public class NioTcpServer {
    public static void main(String[] args) throws Exception {
        // 1. 打开 ServerSocketChannel
        ServerSocketChannel serverChannel = ServerSocketChannel.open();
        serverChannel.configureBlocking(false); // 非阻塞模式

        // 2. 绑定端口
        ServerSocket serverSocket = serverChannel.socket();
        serverSocket.bind(new InetSocketAddress(8888));
        System.out.println("NIO 服务端启动，端口 8888");

        // 3. 创建 Selector（多路复用的核心）
        Selector selector = Selector.open();

        // 4. 将 ServerSocketChannel 注册到 Selector，监听 Accept 事件
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);

        while (true) {
            // 5. 阻塞等待就绪的事件（timeout 防止无限等待）
            selector.select(1000);

            // 6. 获取所有就绪的 SelectionKey
            Set<SelectionKey> keys = selector.selectedKeys();
            Iterator<SelectionKey> iter = keys.iterator();

            while (iter.hasNext()) {
                SelectionKey key = iter.next();
                iter.remove(); // 处理后必须移除，否则会重复处理

                if (key.isAcceptable()) {
                    // 有新的客户端连接请求
                    ServerSocketChannel ssc = (ServerSocketChannel) key.channel();
                    SocketChannel client = ssc.accept();
                    client.configureBlocking(false);

                    // 注册客户端 Channel 到 Selector，监听 Read 事件
                    client.register(selector, SelectionKey.OP_READ,
                            ByteBuffer.allocate(1024));
                    System.out.println("新客户端: " + client.getRemoteAddress());
                }

                if (key.isReadable()) {
                    // 有数据可读
                    SocketChannel client = (SocketChannel) key.channel();
                    ByteBuffer buf = (ByteBuffer) key.attachment();
                    int read = client.read(buf);

                    if (read > 0) {
                        buf.flip();
                        byte[] data = new byte[buf.remaining()];
                        buf.get(data);
                        System.out.println("收到: " + new String(data, "UTF-8"));

                        // Echo 响应
                        String resp = "Echo: " + new String(data, "UTF-8");
                        ByteBuffer respBuf = ByteBuffer.wrap(resp.getBytes("UTF-8"));
                        client.write(respBuf);

                        buf.clear();
                    } else if (read == -1) {
                        // 客户端关闭
                        client.close();
                        System.out.println("客户端关闭: " + client.getRemoteAddress());
                    }
                }
            }
        }
    }
}
```

### 11.5.4 Selector（选择器）

**Selector 是 NIO 多路复用的核心，允许一个线程监控多个 Channel 的 I/O 事件（连接、读、写）。**

#### 11.5.4.1 SelectionKey 的四种事件

| 事件 | 名称 | 含义 |
|------|------|------|
| `OP_ACCEPT` | 接收就绪 | ServerSocketChannel 准备好接受新连接 |
| `OP_CONNECT` | 连接就绪 | SocketChannel 连接到服务端（客户端） |
| `OP_READ` | 读就绪 | 有数据可读 |
| `OP_WRITE` | 写就绪 | 可以写入数据（通道缓冲区可写） |

#### 11.5.4.2 Selector 使用模式

```java
public class SelectorPattern {
    public static void main(String[] args) throws Exception {
        Selector selector = Selector.open();

        // 注册 Channel（必须为非阻塞模式）
        ServerSocketChannel server = ServerSocketChannel.open();
        server.configureBlocking(false);
        server.register(selector, SelectionKey.OP_ACCEPT, null); // attachment 为 null

        // 循环处理事件
        while (selector.select() > 0) {
            for (SelectionKey key : selector.selectedKeys()) {
                if (key.isAcceptable()) {
                    // 处理新连接
                }
                if (key.isReadable()) {
                    // 处理读
                }
                if (key.isWritable()) {
                    // 处理写
                }
                if (key.isConnectable()) {
                    // 处理连接完成
                }

                // 取消注册（不再监听）
                key.cancel();
            }
            selector.selectedKeys().clear();
        }
    }
}
```

#### 11.5.4.3 完整 Echo 服务端（Selector 实现）

```java
public class NioEchoServer {
    public static void main(String[] args) throws Exception {
        ServerSocketChannel serverChannel = ServerSocketChannel.open();
        serverChannel.configureBlocking(false);
        serverChannel.socket().bind(new InetSocketAddress(8888));

        Selector selector = Selector.open();
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);
        System.out.println("NIO Echo 服务端启动，端口 8888");

        ByteBuffer buffer = ByteBuffer.allocate(512);

        while (true) {
            selector.select();
            Set<SelectionKey> keys = selector.selectedKeys();

            for (Iterator<SelectionKey> it = keys.iterator(); it.hasNext(); ) {
                SelectionKey key = it.next();
                it.remove();

                if (key.isAcceptable()) {
                    ServerSocketChannel ssc = (ServerSocketChannel) key.channel();
                    SocketChannel sc = ssc.accept();
                    sc.configureBlocking(false);
                    sc.register(selector, SelectionKey.OP_READ, buffer);
                    System.out.println("连接: " + sc.getRemoteAddress());
                }

                if (key.isReadable()) {
                    SocketChannel sc = (SocketChannel) key.channel();
                    ByteBuffer buf = (ByteBuffer) key.attachment();
                    buf.clear();

                    int read = sc.read(buf);
                    if (read > 0) {
                        buf.flip();
                        String msg = StandardCharsets.UTF_8.decode(buf).toString();
                        System.out.println("收到: " + msg.trim());

                        // Echo 回显
                        buf.flip();
                        sc.write(buf);

                        if ("exit".equals(msg.trim())) {
                            sc.close();
                        }
                    } else if (read == -1) {
                        sc.close();
                    }
                }
            }
        }
    }
}
```

### 11.5.5 NIO 的局限性与 BoringIO

> **重要认知**：虽然 NIO 相比传统 I/O 有了多路复用，但 JDK 原生 NIO 的 API 仍然比较底层，实际使用中容易出错。
>
> **JDK NIO 的常见问题：**
> 1. `Selector` 空轮询 bug（Epoll 空轮询不返回事件，导致 CPU 100%）
> 2. 线程安全问题（Buffer 不是线程安全的）
> 3. 粘包半包需要自行处理
> 4. ByteBuffer 需要手动管理大小，扩容麻烦
>
> 因此，**生产环境推荐使用 Netty、Tomcat（NIO Connector）等成熟框架**，它们在 JDK NIO 基础上封装了更易用的 API，修复了大量 bug。

---

## 11.6 Netty 快速入门

### 11.6.1 Netty 概述

**Netty 是一个基于 NIO 的高性能网络通信框架，由 JBOSS（现 Red Hat）开发，广泛应用于分布式系统中间件（如 Dubbo、RocketMQ）、游戏服务器、大数据通信等领域。**

**Netty vs JDK NIO：**

| 对比项 | JDK NIO | Netty |
|--------|---------|-------|
| API 复杂度 | 底层，繁琐 | 高层封装，简单易用 |
| 线程模型 | 手动管理 | EventLoopGroup 自动管理 |
| 粘包半包 | 自行处理 | 内置多种编解码器 |
| 可靠性 | Bug 多（空轮询） | 经过大规模验证，修复了大量 bug |
| 可扩展性 | 有限 | 责任链模式，高度可扩展 |

### 11.6.2 Maven 依赖

```xml
<dependency>
    <groupId>io.netty</groupId>
    <artifactId>netty-all</artifactId>
    <version>4.1.100.Final</version>
</dependency>
```

### 11.6.3 核心概念

Netty 的核心组件：

| 组件 | 作用 |
|------|------|
| **Bootstrap / ServerBootstrap** | 启动配置类，用于绑定端口和配置连接 |
| **EventLoop** | 单线程执行器，负责处理 Channel 上的所有事件 |
| **EventLoopGroup** | 线程池，包含多个 EventLoop |
| **Channel** | 网络连接的抽象，双向数据流通道 |
| **ChannelHandler** | 业务逻辑处理单元，串联成 Pipeline |
| **ChannelPipeline** | Handler 的责任链，数据依次流过每个 Handler |
| **ByteBuf** | Netty 封装的字节缓冲区（比 ByteBuffer 更强大） |
| **ChannelInitializer** | 初始化 Channel 的 Handler 链 |
| **ChannelFuture** | 异步操作的结果容器 |

### 11.6.4 ByteBuf——增强版 ByteBuffer

Netty 的 ByteBuf 是对 JDK ByteBuffer 的全面升级：

```java
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;

public class ByteBufDemo {
    public static void main(String[] args) {
        // 创建 ByteBuf（堆内）
        ByteBuf buf = Unpooled.buffer(10);
        System.out.println("初始 capacity=" + buf.capacity());

        // 写入数据
        buf.writeBytes("Hello".getBytes());
        System.out.println("写入后 readerIndex=" + buf.readerIndex()
                + ", writerIndex=" + buf.writerIndex());

        // 读取数据
        System.out.print("读取: ");
        while (buf.isReadable()) {
            System.out.print((char) buf.readByte());
        }
        System.out.println();

        // ✅ ByteBuf 的优势：读写索引独立，不需 flip()
        buf.writeBytes("Hello".getBytes());
        buf.readByte(); // 消费一个字节
        buf.readByte(); // 再消费一个字节
        System.out.println("读了两个字节后，readerIndex=" + buf.readerIndex()); // 2

        // 直接内存缓冲区（零拷贝，适合网络传输）
        ByteBuf directBuf = Unpooled.directBuffer(1024);

        // 组合缓冲区（逻辑上组合多个 ByteBuf）
        ByteBuf composite = Unpooled.wrappedBuffer(
                Unpooled.wrappedBuffer("Hello ".getBytes()),
                Unpooled.wrappedBuffer("Netty!".getBytes())
        );
        System.out.println("组合缓冲区内容: "
                + composite.toString(StandardCharsets.UTF_8));
    }
}
```

### 11.6.5 TCP 服务端完整示例

```java
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.*;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.codec.LineBasedFrameDecoder;  // 按行分割，解决粘包
import io.netty.handler.codec.string.StringDecoder;
import io.netty.handler.codec.string.StringEncoder;

public class NettyServer {
    public static void main(String[] args) throws Exception {
        // 1. 创建两个 EventLoopGroup
        // bossGroup：处理 Accept 事件（通常 1 个线程）
        // workerGroup：处理 Read/Write 事件（通常 CPU 核心数 * 2）
        EventLoopGroup bossGroup = new NioEventLoopGroup(1);
        EventLoopGroup workerGroup = new NioEventLoopGroup();

        try {
            // 2. 创建 ServerBootstrap（服务端启动辅助类）
            ServerBootstrap bootstrap = new ServerBootstrap();
            bootstrap.group(bossGroup, workerGroup)       // 绑定线程组
                    .channel(NioServerSocketChannel.class) // 使用 NIO Channel
                    .option(ChannelOption.SO_BACKLOG, 128) // 连接队列大小
                    .childOption(ChannelOption.SO_KEEPALIVE, true) // TCP 保活
                    .childOption(ChannelOption.TCP_NODELAY, true)  // 禁用 Nagle
                    .childHandler(new ChannelInitializer<SocketChannel>() {
                        @Override
                        protected void initChannel(SocketChannel ch) throws Exception {
                            ChannelPipeline pipeline = ch.pipeline();

                            // 添加编解码器（解决字符黏包问题）
                            pipeline.addLast(new LineBasedFrameDecoder(1024));
                            pipeline.addLast(new StringDecoder(StandardCharsets.UTF_8));
                            pipeline.addLast(new StringEncoder(StandardCharsets.UTF_8));

                            // 添加业务 Handler
                            pipeline.addLast(new EchoServerHandler());
                        }
                    });

            // 3. 绑定端口并启动
            ChannelFuture future = bootstrap.bind(8888).sync();
            System.out.println("Netty 服务端启动，端口 8888");

            // 4. 等待服务端 Channel 关闭（即阻塞主线程）
            future.channel().closeFuture().sync();
        } finally {
            // 5. 优雅关闭
            workerGroup.shutdownGracefully();
            bossGroup.shutdownGracefully();
        }
    }
}

// 业务 Handler
class EchoServerHandler extends ChannelInboundHandlerAdapter {
    private static final Logger log = LoggerFactory.getLogger(EchoServerHandler.class);

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) throws Exception {
        String request = (String) msg;
        log.info("收到: {}", request.trim());

        // Echo 响应
        ctx.writeAndFlush("Echo: " + request);
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) throws Exception {
        log.error("异常: {}", cause.getMessage());
        ctx.close();
    }

    @Override
    public void channelActive(ChannelHandlerContext ctx) throws Exception {
        log.info("客户端连接: {}", ctx.channel().remoteAddress());
    }

    @Override
    public void channelInactive(ChannelHandlerContext ctx) throws Exception {
        log.info("客户端断开: {}", ctx.channel().remoteAddress());
    }
}
```

### 11.6.6 TCP 客户端完整示例

```java
import io.netty.bootstrap.Bootstrap;
import io.netty.channel.*;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioSocketChannel;
import io.netty.handler.codec.LineBasedFrameDecoder;
import io.netty.handler.codec.string.StringDecoder;
import io.netty.handler.codec.string.StringEncoder;

public class NettyClient {
    public static void main(String[] args) throws Exception {
        EventLoopGroup group = new NioEventLoopGroup();

        try {
            Bootstrap bootstrap = new Bootstrap();
            bootstrap.group(group)
                    .channel(NioSocketChannel.class)
                    .option(ChannelOption.SO_KEEPALIVE, true)
                    .handler(new ChannelInitializer<SocketChannel>() {
                        @Override
                        protected void initChannel(SocketChannel ch) throws Exception {
                            ChannelPipeline p = ch.pipeline();
                            p.addLast(new LineBasedFrameDecoder(1024));
                            p.addLast(new StringDecoder(StandardCharsets.UTF_8));
                            p.addLast(new StringEncoder(StandardCharsets.UTF_8));
                            p.addLast(new EchoClientHandler());
                        }
                    });

            // 连接服务端
            ChannelFuture future = bootstrap.connect("127.0.0.1", 8888).sync();
            Channel channel = future.channel();

            // 发送消息
            for (int i = 0; i < 5; i++) {
                channel.writeAndFlush("消息 " + i + "\n");
                Thread.sleep(500);
            }

            channel.closeFuture().sync();
        } finally {
            group.shutdownGracefully();
        }
    }
}

class EchoClientHandler extends ChannelInboundHandlerAdapter {
    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) throws Exception {
        System.out.println("收到: " + msg);
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) throws Exception {
        cause.printStackTrace();
        ctx.close();
    }
}
```

### 11.6.7 Netty 的核心组件详解

#### 11.6.7.1 Bootstrap 与 ServerBootstrap

| 配置项 | Bootstrap（客户端） | ServerBootstrap（服务端） |
|--------|-------------------|------------------------|
| 用途 | 连接远程服务端 | 绑定本地端口 |
| 线程组 | 1 个 EventLoopGroup | 2 个（bossGroup + workerGroup） |
| Channel 类型 | NioSocketChannel | NioServerSocketChannel |
| 绑定方式 | `connect()` | `bind()` |

```java
// 客户端 Bootstrap 完整配置
Bootstrap bootstrap = new Bootstrap();
bootstrap.group(group)
        .channel(NioSocketChannel.class)
        .remoteAddress(new InetSocketAddress("127.0.0.1", 8888))
        .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 3000)  // 连接超时
        .option(ChannelOption.SO_KEEPALIVE, true)             // TCP 保活
        .option(ChannelOption.TCP_NODELAY, true)              // 禁用 Nagle
        .handler(new ChannelInitializer<SocketChannel>() {
            @Override
            protected void initChannel(SocketChannel ch) {
                ch.pipeline().addLast(new MyHandler());
            }
        });

ChannelFuture f = bootstrap.connect();
f.addListener((ChannelFutureListener) future -> {
    if (future.isSuccess()) {
        System.out.println("连接成功");
    } else {
        System.err.println("连接失败: " + future.cause());
    }
});
```

#### 11.6.7.2 ChannelHandler 与 ChannelPipeline

Netty 使用**责任链模式**处理数据，每个 Handler 负责一种处理逻辑，数据在 Pipeline 中依次流过每个 Handler：

```
Inbound（入站）:  ChannelPipeline.read() → Handler1 → Handler2 → ... → ChannelInboundHandler
Outbound（出站）: ChannelOutboundHandler → Handler1 → Handler2 → ... → ChannelPipeline.write()
```

```java
// 多个 Handler 按添加顺序执行
pipeline.addLast(new LoggingHandler(LogLevel.INFO));     // 日志（Inbound）
pipeline.addLast(new LineBasedFrameDecoder(1024));        // 帧分割（Inbound）
pipeline.addLast(new StringDecoder(StandardCharsets.UTF_8)); // 解码（Inbound）
pipeline.addLast(new MyBusinessHandler());                // 业务（Inbound）
pipeline.addLast(new StringEncoder(StandardCharsets.UTF_8)); // 编码（Outbound）
pipeline.addLast(new LoggingHandler(LogLevel.INFO));     // 日志（Outbound）
```

#### 11.6.7.3 EventLoop 与 EventLoopGroup

- **EventLoop**：绑定到一个线程的循环，负责处理该 Channel 上的所有 I/O 事件
- **EventLoopGroup**：管理多个 EventLoop，分配给不同的 Channel

```
EventLoopGroup (4个线程)
  ├── EventLoop 1 → Channel A, B
  ├── EventLoop 2 → Channel C
  ├── EventLoop 3 → Channel D, E, F
  └── EventLoop 4 → (空闲)

一个 Channel 的一生都在同一个 EventLoop 中处理（无需加锁）
```

### 11.6.8 TCP 粘包半包问题与解决方案

#### 11.6.8.1 什么是粘包和半包

**粘包**：多个发送方的数据包被合并成一个 TCP 段（发送方 Nagle 算法或接收方缓冲区积累）

```
发送方:  包A        包B         包C
接收方:  [包A包B包C  ]   ← 被合并为一个读取操作
```

**半包**：一个发送方的数据包被拆分成多个 TCP 段（数据量大于 MTU 或接收方缓冲区较小）

```
发送方:  [一个大数据包，超过MTU]
接收方:  [包A][包B]   ← 被拆分成多次读取
```

#### 11.6.8.2 解决方案

**方案1：固定长度（适合消息长度固定的场景）**

```java
pipeline.addLast(new FixedLengthFrameDecoder(10)); // 每个消息固定10字节
```

**方案2：分隔符（适合文本协议，如 HTTP、Redis）**

```java
pipeline.addLast(new LineBasedFrameDecoder(1024));    // 按 \n 分隔
pipeline.addLast(new DelimiterBasedFrameDecoder(1024,
        Delimiters.lineDelimiter()));                  // 按 \r\n 分隔
```

**方案3：长度前缀（推荐，二进制协议常用）**

```java
// 自定义长度前缀解码器
public class LengthFieldDecoder extends ByteToMessageDecoder {
    @Override
    protected void decode(ChannelHandlerContext ctx, ByteBuf in,
                          List<Object> out) throws Exception {
        // 前4字节为长度字段
        if (in.readableBytes() < 4) return;

        in.markReaderIndex();
        int length = in.readInt();

        if (in.readableBytes() < length) {
            in.resetReaderIndex(); // 数据不完整，等待更多数据
            return;
        }

        ByteBuf body = in.readBytes(length);
        out.add(body);
    }
}

// 或使用 Netty 内置的LengthFieldBasedFrameDecoder
pipeline.addLast(new LengthFieldBasedFrameDecoder(
        1024,     // 最大帧长度
        0,        // 长度字段偏移
        4,        // 长度字段长度（4字节）
        0,        // 长度字段后跳过的字节数
        4         // 要剥离的字节数（长度字段本身）
));
```

**方案4：自定义协议（生产环境最常用）**

```java
// 协议格式：[魔数 2字节][版本 1字节][类型 1字节][长度 4字节][数据 N字节][校验 2字节]
public class MyProtocolDecoder extends ByteToMessageDecoder {
    @Override
    protected void decode(ChannelHandlerContext ctx, ByteBuf in,
                          List<Object> out) throws Exception {
        if (in.readableBytes() < 8) return; // 最小头部长度

        in.markReaderIndex();

        short magic = in.readShort();
        if (magic != 0xABCD) {
            throw new IllegalArgumentException("Invalid magic number");
        }

        byte version = in.readByte();
        byte type = in.readByte();
        int length = in.readInt();

        if (in.readableBytes() < length + 2) {
            in.resetReaderIndex();
            return;
        }

        ByteBuf data = in.readBytes(length);
        short checksum = in.readShort();

        // 校验
        if (calculateChecksum(data, checksum)) {
            out.add(new ProtocolMessage(version, type, data));
        }
    }
}
```

### 11.6.9 长连接保活（Keep-Alive）

TCP 层面的 `SO_KEEPALIVE` 只能检测对端崩溃，无法检测应用层无响应。Netty 提供了 `IdleStateHandler` 来做应用层心跳：

```java
// 服务端添加空闲检测 Handler
// 5秒内没有读事件，触发 IdleStateEvent
pipeline.addLast(new IdleStateHandler(5, 0, 0));
pipeline.addLast(new HeartbeatHandler());

// 心跳 Handler
public class HeartbeatHandler extends ChannelInboundHandlerAdapter {
    @Override
    public void userEventTriggered(ChannelHandlerContext ctx, Object evt)
            throws Exception {
        if (evt instanceof IdleStateEvent) {
            System.out.println("心跳超时，关闭连接: " + ctx.channel().remoteAddress());
            ctx.close();
        }
    }
}

// 客户端定期发送心跳
public class ClientHeartbeatHandler extends ChannelOutboundHandlerAdapter {
    @Override
    public void channelActive(ChannelHandlerContext ctx) throws Exception {
        ctx.executor().scheduleAtFixedRate(() -> {
            if (ctx.channel().isActive()) {
                ctx.writeAndFlush("ping\n");
            }
        }, 0, 3, TimeUnit.SECONDS);
    }
}
```

### 11.6.10 异步 I/O 与 Future/Promise 模式

Netty 中所有 I/O 操作都是异步的，返回 `ChannelFuture`：

```java
// 非阻塞式写入
ChannelFuture future = channel.writeAndFlush("Hello\n");
future.addListener((ChannelFutureListener) f -> {
    if (f.isSuccess()) {
        System.out.println("写入成功");
    } else {
        System.err.println("写入失败: " + f.cause());
    }
});

// 也可以用 sync() 阻塞等待完成（但不推荐在 EventLoop 中使用）
// future.sync();

// Promise 模式：主动通知结果（比 Future 更灵活）
ChannelPromise promise = channel.newPromise();
channel.writeAndFlush("test", promise);
promise.addListener(f -> {
    if (f.isSuccess()) {
        System.out.println("写入成功");
    }
});
```

---

## 11.7 常见面试题

### 面试题1：TCP 三次握手和四次挥手，为什么三次握手、四次挥手？

**三次握手原因：**
- 服务端收到 SYN 后可以立即进入 `SYN_RCVD` 状态并发送 SYN+ACK
- 客户端收到 SYN+ACK 后进入 ESTABLISHED 并发送 ACK
- 此时服务端收到 ACK 才进入 ESTABLISHED
- 如果只有两次握手，服务端无法确认客户端收到了自己的 SYN+ACK，可能导致空等

**四次挥手原因：**
- TCP 是全双工，两个方向的数据流需要独立关闭
- 客户端发送 FIN 表示不再发送数据，但还可以接收数据
- 服务端收到 FIN 后回复 ACK，此时进入 `CLOSE_WAIT` 状态
- 服务端处理完数据后再发送 FIN，此时才表示不再发送数据
- 客户端收到 FIN 后回复 ACK，进入 `TIME_WAIT` 状态

### 面试题2：TCP 和 UDP 的区别，如何选择？

| 对比 | TCP | UDP |
|------|-----|-----|
| 连接性 | 面向连接 | 无连接 |
| 可靠性 | 可靠 | 不可靠 |
| 传输方式 | 字节流 | 数据报 |
| 速度 | 较慢 | 快 |
| 头部 | 20-60 字节 | 8 字节 |
| 场景 | 重要数据传输（文件、网页、邮件） | 实时性要求高（视频、语音、游戏） |

**选择原则：** 需要可靠交付用 TCP（如文件传输、API 调用）；对实时性要求高、能容忍少量丢失用 UDP（如直播、游戏）

### 面试题3：HTTP 和 HTTPS 的区别？

| 对比 | HTTP | HTTPS |
|------|------|-------|
| 端口 | 80 | 443 |
| 协议层 | 直接基于 TCP | HTTP + TLS + TCP |
| 安全性 | 明文传输，可被窃听和篡改 | 加密传输，身份认证（证书） |
| 性能 | 略快（无加密开销） | 略慢（TLS 握手） |
| 搜索引擎 | 不推荐 | SEO 加分（Google） |

### 面试题4：TCP 粘包和半包是什么？如何解决？

**粘包**：多个发送方数据包被合并成一个 TCP 段。**半包**：一个发送方数据包被拆分成多个 TCP 段。

**原因：** TCP 是字节流协议，不保留消息边界；接收方缓冲区大小或 Nagle 算法会导致合并/拆分。

**解决方案：**
1. 固定长度（`FixedLengthFrameDecoder`）
2. 分隔符（`LineBasedFrameDecoder`、`DelimiterBasedFrameDecoder`）
3. 长度前缀（`LengthFieldBasedFrameDecoder`，最通用）
4. 自定义协议（推荐生产环境）

### 面试题5：什么是 HTTP 长连接和短连接？

- **短连接**：每个请求/响应后立即关闭 TCP 连接（如 HTTP/1.0 默认）
- **长连接（Keep-Alive）**：多个请求复用同一个 TCP 连接（如 HTTP/1.1 默认）
  - 减少 TCP 连接建立/关闭的开销
  - 头部 `Connection: keep-alive` / `Connection: close`
  - HTTP/2 支持多路复用，一个连接上并行多个请求
  - HTTP/1.1 默认长连接，`Connection: close` 才关闭

### 面试题6：NIO 和 BIO 的区别？

| 对比 | BIO（阻塞 I/O） | NIO（非阻塞 I/O） |
|------|--------------|----------------|
| I/O 模式 | 阻塞（read/write 等待完成） | 非阻塞（立即返回） |
| 线程模型 | 每连接一个线程（或线程池） | 单线程 + Selector 多路复用 |
| 适用场景 | 低并发 | 高并发（C10K+） |
| API | InputStream/OutputStream | Channel/Buffer/Selector |
| 消息边界 | 由 Stream 处理 | 需要自定义协议 |

### 面试题7：Netty 的线程模型是怎样的？

Netty 使用 **Reactor 模式**：
- **BossGroup**：处理 Accept 事件，1 个线程（或配置多个）
- **WorkerGroup**：处理 Read/Write 事件，CPU 核心数 * 2 个线程
- 每个 EventLoop 绑定一个线程，处理分配给它的所有 Channel 的 I/O 事件
- 同一 Channel 的所有事件在同一个 EventLoop 中顺序处理（无锁化设计）

### 面试题8：TCP 的 TIME_WAIT 状态是什么？有什么问题？如何解决？

TIME_WAIT 是主动关闭方在四次挥手最后一次发送 ACK 后进入的状态，持续 2MSL（Maximum Segment Lifetime，通常 60~120 秒）。

**问题：** 高并发短连接场景下，大量 TIME_WAIT 连接占用端口和文件描述符，可能导致无法创建新连接。

**解决方案：**
1. `server.setReuseAddress(true)`（SO_REUSEADDR）
2. 调整内核参数：`net.ipv4.tcp_tw_reuse = 1`
3. 使用连接池复用连接
4. 客户端使用长连接而非短连接

### 面试题9：HTTP 状态码 301 vs 302 vs 307 的区别？

| 状态码 | 名称 | 区别 |
|--------|------|------|
| 301 | Moved Permanently | 永久重定向，GET 方法会缓存，POST 浏览器可能改成 GET |
| 302 | Found | 临时重定向，GET 不缓存，POST 保持 POST（但浏览器行为不一致） |
| 307 | Temporary Redirect | 临时重定向，强制保持原请求方法（POST 还是 POST） |
| 308 | Permanent Redirect | 永久重定向，强制保持原请求方法 |

### 面试题10：Netty 为什么性能高？

1. **IO 多路复用**（Selector），单线程处理多个连接，避免线程创建销毁开销
2. **零拷贝**：DirectByteBuffer + CompositeByteBuf + FileRegion，避免 JVM 堆和内核之间的数据拷贝
3. **内存池**：减少 GC 频率，ByteBuf 循环复用
4. **无锁化设计**：Channel 的事件在同一个 EventLoop 中串行处理，无需加锁
5. **责任链模式**：Handler 可插拔，扩展性强
6. **高效的序列化**：内置 Protobuf 等高效编解码器

---

## 本章小结

本章系统讲解了 Java 网络编程的完整知识体系：

| 知识点 | 核心内容 |
|--------|---------|
| **网络基础** | OSI 七层模型、TCP/IP 四层模型、端口号与协议 |
| **TCP 协议** | 三次握手建立连接、四次挥手断开连接、11 种状态流转、可靠传输原理 |
| **HTTP/HTTPS** | 请求/响应结构、8 种方法、15+ 常见状态码、缓存机制、SSL/TLS 原理 |
| **Socket 编程** | TCP ServerSocket/Socket、UDP DatagramSocket、常见坑点与最佳实践 |
| **NIO** | Channel/Buffer/Selector 三件套、Selector 多路复用模式、完整 Echo 服务端 |
| **Netty** | Bootstrap/ChannelHandler/ByteBuf/EventLoop、TCP 粘包半包解决方案、长连接保活、异步 Future/Promise |

**关键知识点总结：**

| 主题 | 掌握要点 |
|------|---------|
| TCP 连接管理 | 三次握手（同步序列号）、四次挥手（每个方向独立关闭）、TIME_WAIT（2MSL） |
| HTTP 协议 | 无状态请求/响应、请求方法语义、状态码分类、缓存头（Cache-Control/ETag） |
| Socket 编程 | try-with-resources 避免泄漏、协议设计解决消息边界、线程池处理并发 |
| NIO | Buffer 的 position/limit/capacity、Channel 双向读写、Selector 监听四种事件 |
| Netty | Reactor 线程模型、ByteBuf 读写索引独立、Pipeline 责任链、粘包半包解决 |
| 高级主题 | 粘包半包（长度前缀/分隔符）、应用层心跳保活、异步 Future/Promise |

---

**下一章：Ch12 - Java 新特性**