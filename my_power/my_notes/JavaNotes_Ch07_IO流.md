# Ch07 - Java I/O 流

## 摘要

Java I/O 是 Java 编程中最核心的知识点之一，贯穿于文件操作、网络通信、序列化和配置读取等各种场景。本章从最基础的字节流和字符流讲起，逐步深入到缓冲流、转换流、NIO 高性能 I/O 以及对象序列化等高级主题，帮你建立完整的 Java I/O 知识体系。

---

## 7.1 I/O 概述

### 什么是 I/O

I/O（Input/Output）即输入输出，是程序与外部世界（文件、网络、内存等）交换数据的手段。Java 将 I/O 抽象为"流"（Stream）的概念：**流是一组有序的数据序列，以顺序方式读写数据**。

### I/O 分类

Java 的 I/O 系统可以从多个维度进行分类：

| 分类维度 | 类型 | 说明 |
|---------|------|------|
| **按数据方向** | 输入流（Input） | 从外部读取数据到程序 |
| | 输出流（Output） | 从程序写出数据到外部 |
| **按数据单位** | 字节流 | 以字节（byte）为单位，每次读写 1 个或多个字节 |
| | 字符流 | 以字符（char）为单位，适合处理文本数据 |
| **按功能** | 节点流 | 直接与数据源/目标连接（底层流） |
| | 处理流（包装流） | 装饰节点流，提供额外功能（高层流） |

### Java I/O 整体架构

Java I/O 主要分布在以下包中：

| 包 | 职责 |
|---|------|
| `java.io` | 经典 I/O，字节流、字符流、文件操作 |
| `java.nio` | New I/O（JDK 1.4+），Buffer、Channel、Selector |
| `java.nio.file` | JDK 7+ 文件操作，Path、Files、FileVisitor |

### 经典 I/O 与 NIO 对比

| 对比项 | 经典 I/O（java.io） | NIO（java.nio） |
|--------|-------------------|----------------|
| 核心抽象 | Stream（流） | Buffer（缓冲区）、Channel（通道） |
| I/O 模式 | 阻塞式（Blocking） | 非阻塞式（Non-blocking）+ 多路复用 |
| 读单位 | 字节/字符 | 块（Buffer） |
| 适用场景 | 小文件、简单场景 | 大文件、高并发服务器 |
| API 风格 | 字节Input/OutputStream | Buffer、Channel、Selector |

> **提示**：NIO 不是 I/O 的替代，而是补充。很多场景下经典 I/O 足够用，不要过度追求 NIO。

---

## 7.2 字节流（InputStream / OutputStream 及常用实现）

### 核心抽象类

```
java.lang.Object
  └── java.io.InputStream        //字节输入流抽象类
  └── java.io.OutputStream       //字节输出流抽象类
```

**InputStream** 是所有字节输入流的父类，核心方法：

```java
public abstract class InputStream {
    //读取一个字节，返回 0-255，末尾返回 -1
    public abstract int read();

    //读取多个字节到数组，返回实际读取数量，末尾返回 -1
    public int read(byte[] b);

    //读取最多 len 个字节到数组 offset 位置
    public int read(byte[] b, int off, int len);

    //跳过 n 个字节
    public long skip(long n);

    //返回可无阻塞读取的字节数
    public int available();

    //关闭流，释放资源
    public void close();

    //单字节读取（效率低，少用）
    public int read() { ... }
}
```

**OutputStream** 是所有字节输出流的父类，核心方法：

```java
public abstract class OutputStream {
    //写入一个字节
    public abstract void write(int b);

    //写入字节数组
    public void write(byte[] b);

    //写入数组中 offset 开始的 len 个字节
    public void write(byte[] b, int off, int len);

    //刷新缓冲区，强制写出
    public void flush();

    //关闭流
    public void close();
}
```

### FileInputStream 与 FileOutputStream

最常用的文件字节流，直接与文件系统交互。

**FileInputStream 示例**：

```java
//构造方式1：直接传文件路径
FileInputStream fis = new FileInputStream("test.txt");

//构造方式2：传 File 对象
FileInputStream fis = new FileInputStream(new File("test.txt"));

//构造方式3：传文件描述符（FileDescriptor）
FileInputStream fis = new FileInputStream(new FileDescriptor());

//按字节读取（效率低，不推荐）
int data;
while ((data = fis.read()) != -1) {
    System.out.print((char) data);
}

//按字节数组读取（推荐）
byte[] buffer = new byte[1024];
int len;
while ((len = fis.read(buffer)) != -1) {
    System.out.print(new String(buffer, 0, len));
}

fis.close();
```

**FileOutputStream 示例**：

```java
//覆盖模式（默认）
FileOutputStream fos = new FileOutputStream("output.txt");

//追加模式（第二个参数为 true）
FileOutputStream fos = new FileOutputStream("output.txt", true);

//写入单个字节
fos.write(65);  //写入字符 'A'

//写入字节数组
byte[] data = "Hello, Java I/O!".getBytes();
fos.write(data);

//写入部分字节
fos.write(data, 0, 5);  //写入 "Hello"

fos.close();
```

### ByteArrayInputStream 与 ByteArrayOutputStream

操作字节数组的流，无需关闭，不涉及系统资源。

```java
//ByteArrayInputStream：从内存字节数组读取
byte[] data = "Hello".getBytes();
ByteArrayInputStream bais = new ByteArrayInputStream(data);

int b;
while ((b = bais.read()) != -1) {
    System.out.println((char) b);
}

//ByteArrayOutputStream：写入到内存字节数组
ByteArrayOutputStream baos = new ByteArrayOutputStream();
baos.write("Hello ".getBytes());
baos.write("World".getBytes());
baos.writeTo(new FileOutputStream("output.txt"));  //直接写出到文件

//转换为字节数组
byte[] result = baos.toByteArray();
String str = baos.toString();  //直接转为字符串
```

### DataInputStream 与 DataOutputStream

用于读写 Java 基本数据类型，**数据流按二进制格式传输**，不是文本格式。

```java
//DataOutputStream：写入基本类型
DataOutputStream dos = new DataOutputStream(
    new FileOutputStream("data.bin")
);
dos.writeInt(42);           //写入整数
dos.writeDouble(3.14159);   //写入双精度
dos.writeUTF("Hello");      //写入 UTF 字符串
dos.writeBoolean(true);     //写入布尔值
dos.close();

//DataInputStream：读取基本类型
DataInputStream dis = new DataInputStream(
    new FileInputStream("data.bin")
);
int intVal = dis.readInt();           //读取整数
double doubleVal = dis.readDouble();  //读取双精度
String strVal = dis.readUTF();        //读取 UTF 字符串
boolean boolVal = dis.readBoolean();  //读取布尔值
dis.close();

System.out.println(intVal + ", " + doubleVal + ", " + strVal + ", " + boolVal);
//输出：42, 3.14159, Hello, true
```

> **注意**：`DataInputStream` 读取的顺序必须和写入顺序完全一致，否则数据会错乱。

### 常用字节流一览

| 类 | 类型 | 用途 |
|---|---|---|
| `FileInputStream` / `FileOutputStream` | 节点流 | 文件读写 |
| `ByteArrayInputStream` / `ByteArrayOutputStream` | 节点流 | 内存字节数组 |
| `DataInputStream` / `DataOutputStream` | 处理流 | 读写基本类型和 UTF 字符串 |
| `BufferedInputStream` / `BufferedOutputStream` | 处理流 | 带缓冲，提升性能 |
| `ObjectInputStream` / `ObjectOutputStream` | 处理流 | 对象序列化 |
| `PipedInputStream` / `PipedOutputStream` | 节点流 | 管道，用于线程通信 |
| `FilterInputStream` / `FilterOutputStream` | 处理流 | 装饰器基类 |

---

## 7.3 字符流（Reader / Writer 及常用实现）

### 为什么要字符流

Java 中 `char` 在 Unicode 中占 2 个字节。字节流直接操作字节，对文本文件（UTF-8、GBK 等）处理时容易出现**乱码问题**，因为一个字符可能对应多个字节。字符流专门用于处理文本数据，自动处理编码转换。

### 核心抽象类

```
java.lang.Object
  └── java.io.Reader          //字符输入流抽象类
  └── java.io.Writer          //字符输出流抽象类
```

**Reader 核心方法**：

```java
public abstract class Reader {
    //读取单个字符，返回 Unicode 码点，末尾返回 -1
    public int read();

    //读取到字符数组
    public int read(char[] cbuf);

    //读取到数组指定区间
    public int read(char[] cbuf, int off, int len);

    public long skip(long n);
    public void close();
    public boolean ready();  //是否准备好用于无阻塞读取
    public boolean markSupported();  //是否支持 mark/reset
    public void mark(int readAheadLimit);
    public void reset();
}
```

**Writer 核心方法**：

```java
public abstract class Writer {
    //写入单个字符
    public void write(int c);

    //写入字符数组
    public void write(char[] cbuf);

    //写入数组区间
    public void write(char[] cbuf, int off, int len);

    //写入字符串
    public void write(String str);

    //写入字符串区间
    public void write(String str, int off, int len);

    public void flush();
    public void close();
}
```

### FileReader 与 FileWriter

专门用于文本文件读写的字符流，默认使用**系统默认编码**（Windows 下是 GBK，Linux/Mac 是 UTF-8），这是最常见的乱码根源之一。

**FileReader 示例（危险写法）**：

```java
//危险！默认编码取决于操作系统，可能乱码
FileReader fr = new FileReader("text.txt");

//正确做法：指定编码
FileReader fr = new FileReader("text.txt", StandardCharsets.UTF_8);
```

```java
//FileReader 按字符读取
FileReader fr = new FileReader("text.txt", StandardCharsets.UTF_8);
char[] buffer = new char[1024];
int len;
while ((len = fr.read(buffer)) != -1) {
    System.out.print(new String(buffer, 0, len));
}
fr.close();

//FileWriter 写入文本
FileWriter fw = new FileWriter("output.txt", StandardCharsets.UTF_8);
fw.write("你好，Java！\n");
fw.write("这是第二行");
fw.close();

//更简洁的写法
try (FileWriter fw2 = new FileWriter("output.txt", StandardCharsets.UTF_8)) {
    fw2.write("使用 try-with-resources 自动关闭");
}
```

### InputStreamReader 与 OutputStreamWriter

**转换流**：将字节流转换为字符流，是字节流和字符流之间的桥梁。最核心的作用是**指定编码**。

```java
//将字节输入流（FileInputStream）转换为字符输入流
//这是指定文件编码的标准方式
FileInputStream fis = new FileInputStream("chinese.txt");
InputStreamReader isr = new InputStreamReader(fis, StandardCharsets.UTF_8);

char[] buffer = new char[1024];
int len;
while ((len = isr.read(buffer)) != -1) {
    System.out.print(new String(buffer, 0, len));
}
isr.close();

//OutputStreamWriter 类似
FileOutputStream fos = new FileOutputStream("output.txt");
OutputStreamWriter osw = new OutputStreamWriter(fos, StandardCharsets.UTF_8);
osw.write("指定编码写入中文");
osw.close();
```

### BufferedReader 与 BufferedWriter

带缓冲的字符处理流，是**读取文本文件最推荐的方式**，性能比直接用 FileReader 高数倍。

```java
//BufferedReader 读取文本（按行）
try (BufferedReader br = new BufferedReader(
        new FileReader("text.txt", StandardCharsets.UTF_8))) {

    //方式1：逐行读取（最常用）
    String line;
    while ((line = br.readLine()) != null) {
        System.out.println(line);
    }

    //方式2：按字符数组读取
    char[] buffer = new char[1024];
    int len;
    while ((len = br.read(buffer)) != -1) {
        System.out.print(new String(buffer, 0, len));
    }
}

//BufferedWriter 写入文本
try (BufferedWriter bw = new BufferedWriter(
        new FileWriter("output.txt", StandardCharsets.UTF_8))) {

    bw.write("第一行内容");
    bw.newLine();        //换行（跨平台）
    bw.write("第二行内容");
    bw.flush();          //刷新缓冲区
}
```

### PrintWriter

专门用于格式化输出，比 BufferedWriter 更方便。

```java
//直接写入文件（自动缓冲）
try (PrintWriter pw = new PrintWriter(
        new FileWriter("output.txt", StandardCharsets.UTF_8))) {

    pw.println("自动换行的内容");
    pw.print("不换行，");
    pw.print("接着写");
    pw.printf("\n格式化输出：%s, %d, %.2f", "Hello", 42, 3.14159);
}

//PrintWriter 也可包装 OutputStream
try (PrintWriter pw = new PrintWriter(
        new OutputStreamWriter(
            new FileOutputStream("output.txt"), StandardCharsets.UTF_8))) {
    pw.println("通过转换流包装");
}
```

### 常用字符流一览

| 类 | 类型 | 用途 |
|---|---|---|
| `FileReader` / `FileWriter` | 节点流 | 文件文本读写（建议指定编码） |
| `BufferedReader` / `BufferedWriter` | 处理流 | 带缓冲，高效按行读写 |
| `InputStreamReader` / `OutputStreamWriter` | 转换流 | 字节流↔字符流，指定编码 |
| `PrintWriter` | 处理流 | 格式化输出（print/printf/println） |
| `StringReader` / `StringWriter` | 节点流 | 字符串作为数据源/目标 |
| `CharArrayReader` / `CharArrayWriter` | 节点流 | 字符数组操作 |
| `PipedReader` / `PipedWriter` | 节点流 | 管道，线程通信 |

---

## 7.4 File 类与文件操作

### File 类概述

`File` 类代表**文件或目录的路径名**，但**不负责实际读写文件内容**。它只能查询文件属性（大小、修改时间、权限等）和进行文件管理操作（创建、删除、重命名）。

```
java.lang.Object
  └── java.io.File
```

### File 构造与基本操作

```java
//构造 File 对象（路径不要求文件真实存在）
File f1 = new File("test.txt");                    //相对路径
File f2 = new File("/tmp/test.txt");                //绝对路径
File f3 = new File("C:\\Users\\Admin\\test.txt"); //Windows 路径
File f4 = new File("C:/Users/Admin/test.txt");     //正斜杠也支持

//使用父路径 + 子路径构造
File dir = new File("C:/Users/Admin");
File f5 = new File(dir, "test.txt");

//获取路径信息
System.out.println(f1.getName());        //test.txt
System.out.println(f1.getParent());      //null（无父目录）
System.out.println(f1.getPath());       //test.txt
System.out.println(f1.getAbsolutePath()); //完整绝对路径

//判断文件类型
System.out.println(f1.isFile());        //是否为普通文件
System.out.println(f1.isDirectory());   //是否为目录
System.out.println(f1.exists());        //是否存在
System.out.println(f1.isHidden());      //是否隐藏
System.out.println(f1.isAbsolute());    //是否为绝对路径
```

### 文件属性查询

```java
File file = new File("test.txt");

//文件大小（字节）
System.out.println("文件大小: " + file.length() + " bytes");

//最后修改时间
long modTime = file.lastModified();
System.out.println("最后修改: " + new Date(modTime));

//权限判断（Unix 系统更丰富）
System.out.println("可读: " + file.canRead());
System.out.println("可写: " + file.canWrite());
System.out.println("可执行: " + file.canExecute());  //Windows 下总是 true
```

### 文件与目录的创建 / 删除

```java
//创建文件（如果不存在）
File newFile = new File("new.txt");
if (!newFile.exists()) {
    boolean created = newFile.createNewFile();
    System.out.println("创建结果: " + created);
}

//创建目录
File dir = new File("myDir");
if (!dir.exists()) {
    dir.mkdir();        //创建单级目录（父目录必须存在）
    //dir.mkdirs();     //创建多级目录（父目录不存在也一并创建）
}

//创建临时文件
try {
    File tempFile = File.createTempFile("prefix", ".tmp", new File("."));
    tempFile.deleteOnExit();  //JVM 退出时自动删除
} catch (IOException e) {
    e.printStackTrace();
}

//删除文件或空目录（非空目录会失败）
boolean deleted = newFile.delete();
System.out.println("删除结果: " + deleted);

//递归删除非空目录（自己实现）
public void deleteDirectory(File dir) {
    if (dir.isDirectory()) {
        File[] files = dir.listFiles();
        if (files != null) {
            for (File file : files) {
                deleteDirectory(file);
            }
        }
    }
    dir.delete();
}
```

### 目录操作

```java
File dir = new File(".");

System.out.println("=== 目录列表 ===");

//列出直接子项（文件和目录）
String[] names = dir.list();
if (names != null) {
    for (String name : names) {
        System.out.println(name);
    }
}

//列出子项（返回 File 对象，更方便）
File[] files = dir.listFiles();
if (files != null) {
    for (File f : files) {
        String type = f.isDirectory() ? "[DIR]" : "[FILE]";
        System.out.println(type + " " + f.getName());
    }
}

//FilenameFilter 过滤文件名
String[] txtFiles = dir.list((d, name) -> name.endsWith(".txt"));
System.out.println("TXT 文件: " + Arrays.toString(txtFiles));

//FileFilter 过滤 File 对象
File[] largeFiles = dir.listFiles(f -> f.isFile() && f.length() > 1024);
```

### 文件重命名与移动

```java
File src = new File("oldName.txt");
File dest = new File("newName.txt");

//重命名（在同一目录）或移动（跨目录）
//注意：覆盖已有文件需要 dest.delete() 先执行
if (dest.exists()) {
    dest.delete();
}
boolean renamed = src.renameTo(dest);
System.out.println("重命名/移动: " + renamed);
```

### ⚠️ File 类的坑

```java
//坑1：路径不存在时，File 对象不会报错
File fake = new File("/nonexistent/path/file.txt");
System.out.println(fake.exists());  //false，不会报错
fake.delete();                      //返回 false，也不报错

//坑2：delete() 不走回收站，直接删除
//坑3：listFiles() 返回 null（而非空数组）当目录不存在或不可读时
File noPermission = new File("/root");
File[] arr = noPermission.listFiles();  //可能返回 null
//正确写法：
if (arr != null) {
    for (File f : arr) { ... }
}

//坑4：File 不支持递归删除非空目录，必须自己写递归方法
```

---

## 7.5 缓冲流（BufferedInputStream / BufferedReader 等）

### 什么是缓冲流

缓冲流在内存中设立缓冲区，减少实际的 I/O 操作次数，从而显著提升性能。**处理文本数据时优先使用 BufferedReader，处理字节数据时优先使用 BufferedInputStream**。

| 缓冲流 | 对应节点流 | 用途 |
|--------|-----------|------|
| `BufferedInputStream` | `FileInputStream` | 字节输入缓冲 |
| `BufferedOutputStream` | `FileOutputStream` | 字节输出缓冲 |
| `BufferedReader` | `FileReader` | 字符输入缓冲（按行） |
| `BufferedWriter` | `FileWriter` | 字符输出缓冲 |

### BufferedInputStream 与 BufferedOutputStream

```java
//BufferedInputStream 使用
//缓冲区大小默认 8192 字节，可自定义
try (BufferedInputStream bis = new BufferedInputStream(
        new FileInputStream("largefile.bin"), 8192)) {

    byte[] buffer = new byte[8192];
    int len;
    long total = 0;
    while ((len = bis.read(buffer)) != -1) {
        total += len;
    }
    System.out.println("读取总字节数: " + total);
}

//BufferedOutputStream 使用
try (BufferedOutputStream bos = new BufferedOutputStream(
        new FileOutputStream("output.bin"))) {

    byte[] data = "Hello, Buffered I/O!".getBytes();
    bos.write(data);
    bos.flush();  //刷新缓冲区，强制写出
}
```

### BufferedReader 最佳实践

```java
//读取大文件最推荐的方式
try (BufferedReader br = new BufferedReader(
        new InputStreamReader(
            new FileInputStream("bigtext.txt"), StandardCharsets.UTF_8))) {

    //按行读取是最常用的方式
    String line;
    int lineNumber = 0;
    while ((line = br.readLine()) != null) {
        lineNumber++;
        if (line.contains("keyword")) {
            System.out.println("第 " + lineNumber + " 行: " + line);
        }
    }
}

//BufferedWriter 使用
try (BufferedWriter bw = new BufferedWriter(
        new OutputStreamWriter(
            new FileOutputStream("output.txt"), StandardCharsets.UTF_8))) {

    for (int i = 1; i <= 100; i++) {
        bw.write("第 " + i + " 行内容");
        bw.newLine();  //跨平台换行符
    }
    bw.flush();
}
```

### BufferedWriter.newLine() vs "\n"

```java
//Windows 换行符是 \r\n，Unix 是 \n，Mac 是 \r
//使用 newLine() 自动适配当前操作系统

bw.write("Hello" + "\n");      //不推荐，可能在不同系统出错
bw.newLine();                  //推荐，跨平台
```

### 性能对比

```java
//对比：不带缓冲 vs 带缓冲的文件读取时间
public class BufferDemo {
    public static void main(String[] args) throws Exception {
        //先生成测试文件
        File out = new File("test.data");
        try (FileOutputStream fos = new FileOutputStream(out)) {
            for (int i = 0; i < 1_000_000; i++) {
                fos.write(("line " + i + "\n").getBytes());
            }
        }

        //不带缓冲
        long t1 = System.currentTimeMillis();
        try (FileInputStream fis = new FileInputStream(out)) {
            while (fis.read() != -1) { }
        }
        System.out.println("无缓冲: " + (System.currentTimeMillis() - t1) + " ms");

        //带缓冲
        long t2 = System.currentTimeMillis();
        try (BufferedInputStream bis = new BufferedInputStream(
                new FileInputStream(out))) {
            while (bis.read() != -1) { }
        }
        System.out.println("有缓冲: " + (System.currentTimeMillis() - t2) + " ms");
    }
}
//典型结果：无缓冲 8000ms+，有缓冲 50ms以内
```

### 缓冲流原理图

```
无缓冲：程序 ←→ 磁盘（每读1字节操作一次磁盘）

有缓冲：程序 ←→ 内存缓冲区 ←→ 磁盘
         （读时一次读一大块到内存，之后从内存逐字节供给程序）
         （写时先写满缓冲区，缓冲区满了才真正写磁盘）
```

---

## 7.6 转换流（InputStreamReader / OutputStreamWriter）

### 转换流的本质

转换流是**字节流和字符流之间的桥梁**，核心价值在于**指定字符编码**。在处理非 ASCII 字符（中文等）时，编码选择至关重要。

```
字节流（FileInputStream）  →  转换流（InputStreamReader）  →  字符流（Reader）
字符流（Writer）  →  转换流（OutputStreamWriter）  →  字节流（FileOutputStream）
```

### 编码问题详解

```java
//乱码的根本原因：写入编码 ≠ 读取编码

//场景：UTF-8 文件，用 GBK 读取
//字节流方式：FileInputStream 读字节 → 按 GBK 解码 → 乱码
FileInputStream fis = new FileInputStream("utf8.txt");
InputStreamReader isr = new InputStreamReader(fis, "GBK"); //指定错误的编码
//结果：中文全部乱码！

//正确方式：指定相同编码
InputStreamReader isr2 = new InputStreamReader(fis, StandardCharsets.UTF_8);
```

### 常用编码一览

| 编码 | 说明 | 特点 |
|------|------|------|
| `UTF-8` | Unicode 变长编码 | 1-4 字节，ASCII 兼容，中文 3 字节 |
| `GBK` | 中文国标扩展 | 1-2 字节，中文 2 字节 |
| `ISO-8859-1` | Latin-1 | 单字节，无法表示中文 |
| `US-ASCII` | 7 位 ASCII | 最基础编码 |
| `UTF-16` | Unicode 定长 | 2 或 4 字节 |

### 标准输入输出与转换流

```java
//System.in 是 InputStream（字节流），包装为 BufferedReader 按行读
BufferedReader stdin = new BufferedReader(
    new InputStreamReader(System.in, StandardCharsets.UTF_8)
);

System.out.print("请输入: ");
String input = stdin.readLine();  //读取一行
System.out.println("你输入了: " + input);

//Scanner 替代方案（更简单，但性能略低）
Scanner scanner = new Scanner(System.in, StandardCharsets.UTF_8);
String s = scanner.nextLine();
```

### 完整读取文件并指定编码

```java
//标准写法：转换流 + 缓冲流 + 指定编码
public static String readFile(String path, Charset charset) throws IOException {
    StringBuilder sb = new StringBuilder();
    try (BufferedReader br = new BufferedReader(
            new InputStreamReader(
                new FileInputStream(path), charset))) {
        String line;
        while ((line = br.readLine()) != null) {
            sb.append(line).append("\n");
        }
    }
    return sb.toString();
}

//使用
String content = readFile("中文文件.txt", StandardCharsets.UTF_8);
System.out.println(content);
```

### ⚠️ 常见编码坑

```java
//坑1：Java 源文件编码与编译器编码不匹配
//javac -encoding UTF-8 Main.java
//如果源文件是 GBK 编码，不指定会报错

//坑2：URL 中的中文字符需要 URLEncoder.encode()
//坑3：HTTP 响应头的编码声明与实际内容编码必须一致
//坑4：数据库连接字符串中的编码参数
```

---

## 7.7 对象序列化

### 什么是序列化

序列化（Serialization）是将 Java 对象转换为字节序列（字节流），以便存储到文件、通过网络传输或保存到内存中。反序列化（Deserialization）是将字节序列恢复为 Java 对象。

### Serializable 接口

`Serializable` 是标记接口（Marker Interface），实现此接口的类才能被序列化。

```java
import java.io.*;

public class Person implements Serializable {
    private static final long serialVersionUID = 1L;

    private String name;
    private int age;
    private transient String password;  //transient 字段不参与序列化

    public Person(String name, int age, String password) {
        this.name = name;
        this.age = age;
        this.password = password;
    }

    @Override
    public String toString() {
        return "Person{name='" + name + "', age=" + age + ", password='" + password + "'}";
    }
}

//序列化到文件
Person p = new Person("张三", 25, "secret123");
try (ObjectOutputStream oos = new ObjectOutputStream(
        new FileOutputStream("person.ser"))) {
    oos.writeObject(p);
    System.out.println("序列化成功");
}

//反序列化
try (ObjectInputStream ois = new ObjectInputStream(
        new FileInputStream("person.ser"))) {
    Person p2 = (Person) ois.readObject();
    System.out.println("反序列化: " + p2);
    //输出: Person{name='张三', age=25, password='null'} <- password 被跳过了
}
```

### serialVersionUID

```java
//serialVersionUID 用于版本兼容性检查
//序列化时：JVM 根据类结构生成一个指纹（默认）
//反序列化时：JVM 比较指纹，不匹配抛 InvalidClassException

//强烈建议显式声明
private static final long serialVersionUID = 1L;

//版本升级示例：
//v1: private static final long serialVersionUID = 1L;
//v2: 新增字段 address，serialVersionUID = 2L
//旧序列化文件仍可反序列化（新增字段为默认值），但需 serialVersionUID 匹配

//修改类后不更新 serialVersionUID，会导致反序列化失败
//java.io.InvalidClassException: com.example.Person; local class incompatible
```

### transient 关键字

`transient` 修饰的字段**不参与序列化**，反序列化后得到默认值（null/0/false）。

```java
class User implements Serializable {
    String username;        //正常序列化
    transient String token; //不序列化，敏感信息
    transient int cache;     //不序列化，缓存数据

    transient static String staticField;  //static 字段也不序列化（属于类，不属于对象）
}
```

### Externalizable 接口

`Externalizable` 继承自 `Serializable`，但需要**手动控制序列化逻辑**，比 `Serializable` 更灵活但更复杂。

```java
import java.io.*;

public class Product implements Externalizable {
    private String name;
    private double price;

    //必须有无参构造器（反序列化时用）
    public Product() {}

    public Product(String name, double price) {
        this.name = name;
        this.price = price;
    }

    //实现序列化逻辑
    @Override
    public void writeExternal(ObjectOutput out) throws IOException {
        out.writeObject(name);
        out.writeDouble(price);
    }

    //实现反序列化逻辑
    @Override
    public void readExternal(ObjectInput in) throws IOException, ClassNotFoundException {
        this.name = (String) in.readObject();
        this.price = in.readDouble();
    }

    @Override
    public String toString() {
        return "Product{name='" + name + "', price=" + price + "}";
    }

    public static void main(String[] args) throws Exception {
        Product p = new Product("笔记本电脑", 5999.0);

        //序列化
        try (ObjectOutputStream oos = new ObjectOutputStream(
                new FileOutputStream("product.obj"))) {
            p.writeExternal(oos);
        }

        //反序列化
        try (ObjectInputStream ois = new ObjectInputStream(
                new FileInputStream("product.obj"))) {
            Product p2 = new Product();  //先用无参构造创建对象
            p2.readExternal(ois);
            System.out.println(p2);
        }
    }
}
```

### 序列化版本兼容规则

| 类变更 | 兼容 | 说明 |
|--------|------|------|
| 新增字段 | ✅ | 反序列化时新字段取默认值 |
| 删除字段 | ✅ | 旧序列化文件中该字段被忽略 |
| 修改字段类型 | ❌ | serialVersionUID 不同时直接失败 |
| 修改字段名 | ⚠️ | 可能导致 InvalidClassException |
| 修改 `serialVersionUID` | ❌ | 与旧序列化文件不兼容 |

### ⚠️ 序列化常见坑

```java
//坑1：对象引用导致重复序列化
class A implements Serializable {
    B b = new B();
}
class B implements Serializable { }

//当 A 被序列化时，B 也会被序列化，没问题
//但如果有循环引用 A.b = a; a.b = a; -> StackOverflowError!

//坑2：单例模式序列化破坏
class Singleton implements Serializable {
    public static final Singleton INSTANCE = new Singleton();
    private Object readResolve() {
        return INSTANCE;  //防止反序列化创建新实例
    }
}

//坑3：父类未实现 Serializable
//子类实现了 Serializable，但父类字段不序列化
class Parent { int x = 1; }
class Child extends Parent implements Serializable { int y = 2; }
//序列化 Child 时，x 不会序列化（丢失）

//坑4：集合序列化
List<Person> people = new ArrayList<>();
people.add(new Person("张三", 20, "pwd"));
//整个 ArrayList 作为一个整体序列化，元素逐一序列化
```

---

## 7.8 NIO 概述（Buffer / Channel / Path / Files）

### NIO vs 经典 I/O

| 对比项 | 经典 I/O | NIO |
|--------|---------|-----|
| 核心抽象 | Stream | Buffer + Channel |
| 读取方式 | 字节/字符流，顺序读取 | Buffer 缓冲区，支持任意位置访问 |
| 模式 | 阻塞式 | 非阻塞 + Selector 多路复用 |
| 通道 | 无 | 双向通道（可同时读写） |
| 缓冲区 | 无 | 核心概念，堆内/堆外内存 |

### Buffer（缓冲区）

`Buffer` 是 NIO 的核心，用于读写数据。本质是一块**有读写位置的连续内存**。

```
Buffer 结构：
┌──────────────────────────────────────────┐
│  capacity: 缓冲区总容量                    │
│  limit:   有效数据终点（写模式下=capacity）  │
│  position: 当前读写位置                     │
│  mark:    书签位置（可选）                   │
└──────────────────────────────────────────┘

初始化后：position=0, limit=capacity, mark=-1
写入后：position 前进，limit 不变，直到 flip()
flip()后：limit=position, position=0，开始读
clear()后：position=0, limit=capacity，可重新写入
```

```java
import java.nio.ByteBuffer;

//创建直接缓冲区（使用操作系统内存，性能更好）
ByteBuffer directBuf = ByteBuffer.allocateDirect(1024);

//创建堆缓冲区（JVM 堆内存）
ByteBuffer heapBuf = ByteBuffer.allocate(1024);

//包装已有字节数组（不拥有数据）
byte[] array = new byte[1024];
ByteBuffer wrappedBuf = ByteBuffer.wrap(array);

//基本操作
ByteBuffer buf = ByteBuffer.allocate(10);

buf.put((byte) 1);        //写：position++
buf.put((byte) 2);
buf.put((byte) 3);

System.out.println("写入后 position=" + buf.position() + ", limit=" + buf.limit());
//position=3, limit=10

buf.flip();                //切换为读模式
System.out.println("flip后 position=" + buf.position() + ", limit=" + buf.limit());
//position=0, limit=3

byte b1 = buf.get();       //读：position++
byte b2 = buf.get();
System.out.println("读取: " + b1 + ", " + b2);

buf.flip();                //再切为写模式（rewind 也可但 mark 会丢）

//其他方法
buf.compact();             //压缩：未读完的数据移到开头，position=未读数据量
buf.rewind();              //重读：position=0, mark=-1
buf.clear();               //清空：position=0, limit=capacity（数据不清，只是覆盖）
buf.mark();                //标记当前位置
buf.reset();               //回到标记位置
```

### 字符集编码（Charset）

```java
import java.nio.charset.Charset;
import java.nio.ByteBuffer;

//字符串与 ByteBuffer 互转
Charset utf8 = StandardCharsets.UTF_8;

String str = "你好，Java NIO！";
ByteBuffer buf = utf8.encode(str);  //String → ByteBuffer

String decoded = utf8.decode(buf).toString();  //ByteBuffer → String

//遍历字节
buf.flip();
while (buf.hasRemaining()) {
    byte b = buf.get();
    System.out.print(b + " ");
}
```

### Channel（通道）

`Channel` 是连接数据源和目标的**双向通道**，与 Stream 的单向不同。常用实现：`FileChannel`、`SocketChannel`、`ServerSocketChannel`、`DatagramChannel`。

**FileChannel 示例**：

```java
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;

public class FileChannelDemo {
    public static void main(String[] args) throws Exception {
        //读写模式打开文件
        RandomAccessFile raf = new RandomAccessFile("data.txt", "rw");
        FileChannel channel = raf.getChannel();

        //写入
        ByteBuffer writeBuf = ByteBuffer.allocate(1024);
        writeBuf.put("Hello, FileChannel!".getBytes());
        writeBuf.flip();  //切换读模式

        channel.write(writeBuf);  //写入文件
        System.out.println("写入完成，位置=" + channel.position());

        //读取
        writeBuf.clear();
        channel.position(0);  //回到开头

        ByteBuffer readBuf = ByteBuffer.allocate(1024);
        int bytesRead = channel.read(readBuf);  //返回读取字节数
        readBuf.flip();
        String content = new String(readBuf.array(), 0, readBuf.remaining());
        System.out.println("读取: " + content);

        //强制刷新到磁盘
        channel.force(true);

        raf.close();
    }
}
```

**FileChannel 的文件锁**：

```java
FileChannel channel = new RandomAccessFile("shared.txt", "rw").getChannel();

//获取独占锁（其他进程无法写）
FileLock lock = channel.lock();
//... 操作文件 ...
lock.release();

//获取共享锁（允许其他进程读）
FileLock sharedLock = channel.lock(0L, Long.MAX_VALUE, true);
sharedLock.release();
```

### Path 与 Files（JDK 7+）

`java.nio.file.Path` 和 `java.nio.file.Files` 是对 `File` 类的现代化替代，API 更简洁直观。

```java
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;

//Path 构造
Path p1 = Paths.get("dir", "subdir", "file.txt");      //推荐写法
Path p2 = Paths.get("/home/user/file.txt");
Path p3 = new File("file.txt").toPath();               //File 转 Path

//Path 操作
Path p = Paths.get("/home/user/documents/report.pdf");
System.out.println("文件名: " + p.getFileName());      //report.pdf
System.out.println("父目录: " + p.getParent());        ///home/user/documents
System.out.println("根目录: " + p.getRoot());          /// (Unix) 或 C:\ (Windows)
System.out.println("路径组件数: " + p.getNameCount());  //3

//路径拼接
Path combined = Paths.get("/home").resolve("user/file.txt");

//路径规范化（移除冗余 . 和 ..）
Path normalized = Paths.get("/home/../home/./user/./file.txt").normalize();

//Files 工具类 - 常用方法
Path filePath = Paths.get("test.txt");

//读取文件所有行
List<String> lines = Files.readAllLines(filePath, StandardCharsets.UTF_8);

//读取全部字节
byte[] bytes = Files.readAllBytes(filePath);

//写入文件（覆盖）
Files.write(filePath, "Hello".getBytes(), StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);

//写入多行
List<String> content = Arrays.asList("第一行", "第二行", "第三行");
Files.write(filePath, content, StandardCharsets.UTF_8, StandardOpenOption.CREATE);

//判断文件类型
System.out.println(Files.isRegularFile(filePath));
System.out.println(Files.isDirectory(filePath));
System.out.println(Files.isReadable(filePath));
System.out.println(Files.isWritable(filePath));

//文件复制
Files.copy(Paths.get("source.txt"), Paths.get("dest.txt"), StandardCopyOption.REPLACE_EXISTING);

//移动文件
Files.move(Paths.get("old.txt"), Paths.get("new.txt"), StandardCopyOption.REPLACE_EXISTING);

//删除文件
Files.delete(filePath);
boolean deleted = Files.deleteIfExists(filePath);  //存在才删

//创建文件/目录
Files.createFile(filePath);
Files.createDirectory(Paths.get("newDir"));
Files.createDirectories(Paths.get("a/b/c"));  //多级创建

//临时文件/目录
Path tempFile = Files.createTempFile("prefix", ".tmp");
Path tempDir = Files.createTempDirectory("prefix");
tempFile.toFile().deleteOnExit();
```

### FileVisitor（遍历目录树）

```java
import java.nio.file.*;
import java.nio.file.attribute.*;

public class FileVisitorDemo {
    public static void main(String[] args) throws Exception {
        Path start = Paths.get("/tmp");

        Files.walkFileTree(start, new SimpleFileVisitor<Path>() {
            @Override
            public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) {
                System.out.println("进入目录: " + dir);
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                System.out.println("  文件: " + file.getFileName() +
                    " (" + attrs.size() + " bytes)");
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult postVisitDirectory(Path dir, IOException exc) {
                System.out.println("离开目录: " + dir);
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFileFailed(Path file, IOException exc) {
                System.err.println("访问失败: " + file + " - " + exc.getMessage());
                return FileVisitResult.CONTINUE;  //继续遍历其他文件
            }
        });
    }
}
```

### NIO 小结对比表

| NIO 组件 | 说明 | 类比 |
|---------|------|------|
| `Buffer` | 有序字节数组，带 position/limit | 水杯 |
| `Channel` | 双向数据传输通道 | 水管 |
| `Selector` | 多路复用器，监控多个 Channel | 多路监控器 |
| `Path` | 文件/目录路径（取代 File） | 路径字符串 |
| `Files` | 文件操作工具类 | 静态工具方法集合 |

---

## 7.9 I/O 优化与常见面试题

### 7.9.1 I/O 优化策略

**1. 减少 I/O 次数**

```java
//错误：频繁 I/O，每次写一个字符
FileWriter fw = new FileWriter("bad.txt");
for (int i = 0; i < 10000; i++) {
    fw.write('a');  //每次都可能有系统调用
}
fw.close();

//正确：缓冲或一次性写入
BufferedWriter bw = new BufferedWriter(new FileWriter("good.txt"));
for (int i = 0; i < 10000; i++) {
    bw.write('a');
}
bw.close();

//最佳：一次性写入（数据量可接受时）
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 10000; i++) {
    sb.append('a');
}
Files.write(Paths.get("best.txt"), sb.toString().getBytes());
```

**2. 使用缓冲流**

```java
//始终使用 BufferedXxxStream / BufferedReader/Writer
//除非数据量很小（小于缓冲区大小），否则性能差异巨大
try (BufferedInputStream bis = new BufferedInputStream(
        new FileInputStream("input.bin"), 8192)) {
    // ...
}
```

**3. 选择合适的数据结构**

```java
//边读边处理，避免一次性加载大文件到内存
try (BufferedReader br = new BufferedReader(
        new InputStreamReader(
            new FileInputStream("huge.txt"), StandardCharsets.UTF_8))) {
    br.lines()                        //Java 8+ 流式处理
      .parallel()                     //并行（注意线程安全）
      .filter(line -> line.contains("keyword"))
      .forEach(System.out::println);
}
```

**4. 直接内存 vs 堆内存**

```java
//直接缓冲区：绕过 JVM 堆，数据在内核空间和直接内存之间传输
//适合大文件（>100MB）或高并发网络 I/O
ByteBuffer directBuffer = ByteBuffer.allocateDirect(1024 * 1024 * 100); //100MB

//注意：直接内存不在堆上，不受 GC 管理，需手动释放
//在 NIO Channel 中使用，不要自己管理生命周期
```

### 7.9.2 常见面试题

**Q1：字节流和字符流的区别？**

> 字节流以 `byte` 为单位，适用于所有数据类型（图片、音频、二进制文件）；字符流以 `char` 为单位，基于 Unicode，专用于文本处理。字符流在底层仍然依赖字节流，但会自动处理编码转换。处理文本数据优先用字符流，其他数据用字节流。

**Q2：I/O 流为什么要关闭？不关闭会怎样？**

> I/O 流占用系统资源（文件描述符、内存）。不关闭可能导致：资源泄漏 → 文件句柄耗尽 → 无法打开新文件。**最佳实践：使用 try-with-resources** 自动关闭。

```java
//错误：可能不关闭
FileInputStream fis = new FileInputStream("a.txt");
... //如果中间抛异常，fis 永远不会关闭

//正确：try-with-resources（自动关闭）
try (FileInputStream fis = new FileInputStream("a.txt")) {
    // ...
} //自动调用 close()

//错误的手动关闭
FileInputStream fis2 = null;
try {
    fis2 = new FileInputStream("a.txt");
} finally {
    if (fis2 != null) fis2.close();  //不够简洁
}
```

**Q3：BufferedReader 的 readLine() 返回值包含换行符吗？**

> **不包含**。`readLine()` 返回的字符串不包含行终止符（`\n`、`\r\n`、`\r`），只包含行内容本身。如果需要保留换行，需要自行添加。

**Q4：File 类和 Path/Files 类的区别？**

> `File` 是 Java 1.0 的遗留 API，设计有缺陷（很多方法返回 boolean 不区分具体错误）；`Path` 和 `Files` 是 JDK 7 引入的现代化 API，更简洁、更一致、功能更丰富。**推荐使用 Path/Files**。

**Q5：什么是装饰器模式？有哪些应用？**

> 装饰器模式：不改变接口，但动态添加功能。Java I/O 中 `BufferedInputStream` 包装 `FileInputStream` 就是装饰器模式。好处是功能可以自由组合（叠加多层装饰）。
>
> ```
> FileInputStream（底层）
>   → BufferedInputStream（加缓冲）
>   → DataInputStream（加数据类型解析）
> ```

**Q6：NIO 的三大核心组件是什么？**

> **Buffer**（缓冲区）、**Channel**（通道）、**Selector**（选择器）。Buffer 是数据容器，Channel 是传输通道，Selector 用于单线程管理多路非阻塞 I/O。

**Q7：Serializable 的 serialVersionUID 有什么用？不声明会怎样？**

> `serialVersionUID` 是类的版本标识，用于反序列化时验证发送方和接收方的类版本是否一致。不显式声明时，JVM 会根据类的结构自动生成一个，但只要类结构发生变化（如增删字段），UID 就会改变，导致反序列化失败。**强烈建议显式声明**。

**Q8：transient 和 static 字段为什么不参与序列化？**

> `transient`：明确标记为不持久化的敏感/临时数据。`static`：属于类而非对象，所有实例共享同一个字段，序列化对象时不能也不应该序列化类级别的数据。

**Q9：try-with-resources 可以用于任何资源吗？**

> 只要资源实现了 `AutoCloseable` 接口即可，不仅仅是 I/O 流。数据库连接（`Connection`）、线程（`Thread`）、锁（`Lock`）等都可以使用。

```java
try (Connection conn = dataSource.getConnection();
     Statement stmt = conn.createStatement()) {
    // 自动关闭 conn 和 stmt
}
```

**Q10：RandomAccessFile 的特点？**

> 支持**随机访问**（文件指针 Seek），可以在文件任意位置读写，不同于只支持顺序读写的流。它既可以读也可以写（通过构造方法的模式参数控制），适用于多线程断点续传、修改文件中间部分等场景。

```java
RandomAccessFile raf = new RandomAccessFile("data.bin", "rw");
raf.seek(100);  //跳到第 100 字节
raf.writeInt(42);
raf.close();
```

### 7.9.3 I/O 操作检查清单

```
□ 文件路径是否存在？
□ 字符编码是否明确指定（避免依赖系统默认）？
□ 是否使用了 try-with-resources？
□ 大文件是否使用了缓冲流？
□ 序列化类是否显式声明了 serialVersionUID？
□ transient 字段是否符合预期？
□ 文件读取是否处理了 null 返回（listFiles）？
□ 写入后是否需要 flush？
```

---

## 本章小结

本章系统梳理了 Java I/O 的知识体系：

| 知识点 | 核心要点 |
|--------|---------|
| **字节流** | InputStream/OutputStream，以字节为单位，适用于所有数据类型 |
| **字符流** | Reader/Writer，以字符为单位，处理文本必须指定编码 |
| **File 类** | 操作文件属性和目录，不负责读写内容 |
| **缓冲流** | 减少 I/O 次数，文本读取用 BufferedReader，按行最方便 |
| **转换流** | InputStreamReader/OutputStreamWriter，字节↔字符桥梁，指定编码 |
| **对象序列化** | Serializable + serialVersionUID，transient 字段不序列化 |
| **NIO** | Buffer（position/limit/capacity）、Channel（双向）、Path/Files |
| **try-with-resources** | 自动关闭资源，推荐写法，避免资源泄漏 |

---

**下一章：Ch08 - 集合进阶**
