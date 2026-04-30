# 第 10 章 JVM 虚拟机

> 本章摘要：JVM（Java Virtual Machine）是 Java 技术的核心，也是面试中最能拉开差距的模块之一。本章从 JVM 整体结构讲起，涵盖类加载机制、运行时数据区、垃圾回收算法与收集器、JVM 调优实战命令，最后梳理高频面试题，帮你建立完整的 JVM 知识体系。

---

## 10.1 JVM 概述与整体结构

### 10.1.1 什么是 JVM

JVM 是运行 Java 字节码的虚拟计算机。它屏蔽了底层硬件和操作系统的差异，使得「一次编写，到处运行」成为可能。

**JVM 与 JDK、JRE 的关系：**

```
JDK (Java Development Kit)
├── JRE (Java Runtime Environment)
│   ├── JVM (Java Virtual Machine)
│   └── 核心类库
└── 开发工具（javac、jar 等）
```

### 10.1.2 JVM 整体结构

```
┌──────────────────────────────────────────────┐
│                  程序运行时                     │
│  ┌────────────────────────────────────────┐  │
│  │              类加载子系统                 │  │
│  │         (ClassLoader Subsystem)         │  │
│  └────────────────┬───────────────────────┘  │
│                   │ 加载后的字节码              │
│  ┌────────────────▼───────────────────────┐  │
│  │             执行引擎 (Execution Engine)   │  │
│  │  ┌────────────┬───────────┬──────────┐  │  │
│  │  │ 解释器     │ JIT编译器  │ GC组件    │  │  │
│  │  │ (Interpreter)│(JIT)     │         │  │  │
│  │  └────────────┴───────────┴──────────┘  │  │
│  └────────────────┬───────────────────────┘  │
│                   │                       │
│  ┌────────────────▼───────────────────────┐  │
│  │           运行时数据区 (Runtime Data Areas)│  │
│  │  ┌─────────┐ ┌──────┐ ┌─────────────┐  │  │
│  │  │ 堆(Heap)│ │方法区 │ │ 程序计数器   │  │  │
│  │  │        │ │(Method│ │(PC Register)│  │  │
│  │  │        │ │ Area) │ │            │  │  │
│  │  ├─────────┤├───────┤├─────────────┤  │  │
│  │  │虚拟机栈 │ │运行时常 │ │ 本地方法栈  │  │  │
│  │  │(VM Stack)│ │量池    │ │(Native     │  │  │
│  │  │        │ │       │ │ Method Stack)│  │  │
│  │  └─────────┘ └───────┘ └─────────────┘  │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

### 10.1.3 各组件职责速览

| 组件 | 线程共享 | 存储内容 | 异常场景 |
|------|---------|---------|---------|
| **堆 (Heap)** | ✅ | 对象实例、数组 | `OutOfMemoryError: Heap` |
| **方法区 (Method Area)** | ✅ | 类信息、常量、静态变量、JIT 编译产物 | `OutOfMemoryError: PermGen/Metaspace` |
| **程序计数器 (PC Register)** | ❌ | 当前线程执行的字节码行号 | 无 |
| **虚拟机栈 (VM Stack)** | ❌ | 方法调用栈帧（局部变量表、操作数栈等） | `StackOverflowError` / `OutOfMemoryError` |
| **本地方法栈 (Native Method Stack)** | ❌ | Native 方法调用栈 | `StackOverflowError` / `OutOfMemoryError` |

> **注意：** JDK 8 及之后，永久代（PermGen）被元空间（Metaspace）取代。元空间使用本地内存，大小可以动态扩展。

### 10.1.4 Java 代码执行流程

```
.java 源码
   │  javac 编译
   ▼
.class 字节码文件
   │  类加载器 (ClassLoader)
   ▼
JVM 内部数据结构 (Class 对象)
   │
   ├── 解释执行 (字节码 → 机器码，逐行)
   └── JIT 编译 (热点代码 → 编译成机器码，缓存)
         │
         ▼
      执行引擎 → 运行时数据区
```

> **热点代码探测：** JIT 编译器通过热点计数器识别高频执行的方法和循环，将它们编译为本地机器码，大幅提升执行效率。这是 JVM 性能优化的核心机制之一。

---

## 10.2 类加载机制

### 10.2.1 类加载生命周期

一个类从被加载到 JVM 开始，到被卸载出内存为止，整个生命周期如下：

```
加载 (Loading)
  → 验证 (Verification)
    → 准备 (Preparation)
      → 解析 (Resolution)
        → 初始化 (Initialization)
          → 使用 (Using)
            → 卸载 (Unloading)
```

其中 **验证、准备、解析** 合称为**链接（Linking）**。

### 10.2.2 各阶段详解

#### 1. 加载（Loading）

- 通过类的全限定名获取定义类的二进制字节流
- 将字节流转化为方法区的运行时数据结构
- 在堆中生成对应的 `java.lang.Class` 对象，作为方法区数据的访问入口

#### 2. 验证（Verification）

确保字节码符合 JVM 规范，不会危害 JVM 安全。验证阶段包含：

| 验证类型 | 检查内容 |
|---------|---------|
| 文件格式验证 | 魔数 0xCAFEBABE、版本号等 |
| 元数据验证 | 语义分析（是否有父类、final 类是否被继承等） |
| 字节码验证 | 数据流、控制流是否合法 |
| 符号引用验证 | 能否找到对应的类、方法、字段 |

#### 3. 准备（Preparation）

**为类变量分配内存并设置默认初始值。**

```java
// 准备阶段：a=0, b=null（默认值）
public static int a = 10;
public static String b = "hello";
```

> ⚠️ **常见坑：** `static final` 修饰的编译期常量（如 `public static final int a = 10`）在准备阶段就会直接赋值为 10，因为编译时已经确定，不需要等到初始化阶段。但如果 `static final` 赋值的是一个方法调用结果，则仍在初始化阶段赋值。

#### 4. 解析（Resolution）

将常量池中的**符号引用**替换为**直接引用**。

- 符号引用：用字符串表示，不受 JVM 内存位置约束
- 直接引用：指向目标在内存中的实际地址

```java
// 解析前：符号引用 "java.lang.String"
// 解析后：直接引用 → 指向方法区中 String 类信息的指针
```

#### 5. 初始化（Initialization）

**执行类构造器 `<clinit>()` 方法**，为类变量赋实际值。

```java
public class InitDemo {
    // <clinit> 中执行：a = 10, b = "world"
    public static int a = 10;
    public static String b = "world";
}
```

> ⚠️ **触发初始化的时机（主动引用）：**
> 1. `new`、读取或修改类的静态字段（final 修饰的编译期常量除外）
> 2. 调用类的静态方法
> 3. `reflect` 操作
> 4. 初始化子类时，父类尚未初始化（先初始化父类）
> 5. 主类（包含 `main()` 方法的类）
> 6. 动态语言支持相关的 `MethodHandle` 实例

### 10.2.3 双亲委派模型

#### 什么是双亲委派

当类加载器收到加载请求时，它**首先将请求委派给父类加载器处理**，层层向上，直到最顶层。如果父加载器无法完成，才由自己尝试加载。

```
Bootstrap ClassLoader (C++ 实现，无对应 Java 对象)
    ↑
Extension ClassLoader (ExtClassLoader)
    ↑
Application ClassLoader (AppClassLoader / System ClassLoader)
    ↑
自定义 ClassLoader
```

**加载顺序示例：**

```java
// 用户代码尝试加载 java.lang.String
// → Application ClassLoader 收到请求
//     → 委派给 Extension ClassLoader
//         → 委派给 Bootstrap ClassLoader
//             → Bootstrap 无法加载 java.lang.String（它由 Bootstrap 加载）
//         → Extension ClassLoader 尝试加载（也失败）
//     → Application ClassLoader 自己尝试加载
//         → 失败（String 不在 classpath 中以这个路径存在）
// 最终抛出 ClassNotFoundException
```

> 实际上 `java.lang.String` 是由 Bootstrap ClassLoader 加载的，这里只是演示流程。

#### 为什么要双亲委派

1. **安全性：** 防止核心 API 被篡改。例如自定义 `java.lang.String` 类不会被加载。
2. **避免重复加载：** 父加载器已加载的类，子加载器不会再次加载，保证类的唯一性。
3. **保证类的层级关系：** 类的身份由其 ClassLoader 共同决定，全限定名相同但 ClassLoader 不同，是不同的类。

#### 如何破坏双亲委派

**场景 1：JDBC 驱动加载（SPI 机制）**

JDBC 使用 `ServiceLoader.load()`，由线程上下文类加载器（ContextClassLoader）打破双亲委派。

```java
// JDBC 4.0 之后，使用 META-INF/services 注册
// DriverManager 内部使用 ContextClassLoader 加载
ServiceLoader<Driver> loader = ServiceLoader.load(Driver.class);
```

**场景 2：Tomcat 的类隔离**

Tomcat 需要在同一 JVM 中运行多个 Web 应用，每个应用需要独立的类版本。Tomcat 为每个 Webapp 自定义类加载器（`WebappClassLoader`），优先加载本地类，不向上委派。

**场景 3：自定义 ClassLoader**

```java
// 自定义 ClassLoader，重写 loadClass 方法即可打破双亲委派
public class MyClassLoader extends ClassLoader {
    @Override
    protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
        if (name.startsWith("com.myapp.")) {
            // 直接用自己的 findClass，不委派
            byte[] classData = findClassBytes(name);
            return defineClass(name, classData, 0, classData.length);
        }
        // 其他类走双亲委派
        return super.loadClass(name, resolve);
    }
}
```

### 10.2.4 类加载器种类

| 类加载器 | 加载路径 | 说明 |
|---------|---------|------|
| Bootstrap ClassLoader | `$JAVA_HOME/jre/lib/` | JVM 底层实现，C++，无法直接访问 |
| Extension ClassLoader | `$JAVA_HOME/jre/lib/ext/` | 加载扩展目录中的类 |
| Application ClassLoader | `CLASSPATH`、`-cp` | 加载用户编写的类 |
| 自定义 ClassLoader | 任意路径 | 用户自行实现 |

---

## 10.3 运行时数据区

### 10.3.1 堆（Heap）

堆是 JVM 中**最大的一块内存区域**，被所有线程共享，用于存储对象实例和数组。

```
┌──────────────────────────────────────┐
│               堆 (Heap)                │
│  ┌──────────────┐ ┌──────────────┐   │
│  │   新生代      │ │   老年代      │   │
│  │ (Young Gen)  │ │ (Old Gen)    │   │
│  │ ┌────┐┌────┐│ │              │   │
│  │ │Eden││S0/S1││ │              │   │
│  │ └────┘└────┘│ │              │   │
│  └──────────────┘ └──────────────┘   │
└──────────────────────────────────────┘
```

**内存比例（JDK 默认）：**

- 新生代 : 老年代 = **1 : 2**
- 新生代中 Eden : Survivor0 : Survivor1 = **8 : 1 : 1**

**代码示例：对象分配位置**

```java
public class Heap分配 {
    // 成员变量在堆中
    private int[] data = new int[1024];

    public void allocate() {
        //局部变量在栈上，但 new 的对象在堆上
        Object obj = new Object();
    }
}
```

> 💡 **实战技巧：** 使用 `-Xms256m -Xmx512m` 设置堆初始和最大大小，生产环境建议设置为相同值，避免频繁扩容收缩。

### 10.3.2 虚拟机栈（VM Stack）

每个线程拥有独立的虚拟机栈，**线程栈**。每个方法调用创建一个**栈帧（Stack Frame）**，方法执行完成栈帧出栈。

**栈帧结构：**

```
┌─────────────────────────────┐
│      栈帧 (Stack Frame)       │
│  ┌─────────────────────────┐ │
│  │  局部变量表 (Local Vars)  │ │ ← 方法参数、局部变量
│  ├─────────────────────────┤ │
│  │  操作数栈 (Operand Stack) │ │ ← 字节码指令操作数
│  ├─────────────────────────┤ │
│  │  动态链接 (Dynamic Link)  │ │ → 指向常量池的符号引用
│  ├─────────────────────────┤ │
│  │  返回地址 (Return Address)│ │ → 方法正常/异常退出地址
│  └─────────────────────────┘ │
└─────────────────────────────┘
```

**常见异常：**

```java
public class StackDemo {
    // 递归没有终止条件 → StackOverflowError
    public static int recursive(int n) {
        return recursive(n + 1); // 无限递归
    }

    public static void main(String[] args) {
        recursive(1);
    }
}
```

```java
// 创建大量线程 → OutOfMemoryError (unable to create new native thread)
// -Xss256k 设置每线程栈大小（默认 1MB）
```

> ⚠️ **最佳实践：** 递归调用一定要设置递归深度限制（可以用尾递归优化或改用循环）。单线程场景下，栈空间比堆更容易耗尽。

### 10.3.3 方法区（Method Area）

存储类的元信息（类名、访问修饰符、字段描述、方法描述等）、常量、静态变量、JIT 编译后的代码。

**JDK 8 变化：**

| 版本 | 实现 |
|------|------|
| JDK 7 及之前 | 永久代（PermGen Space）— 使用 JVM 堆内存 |
| JDK 8 及之后 | 元空间（Metaspace）— 使用本地内存（Native Memory） |

```java
// 方法区中存储的内容
public class MethodAreaDemo {
    // 静态变量 → 方法区
    public static int staticVar = 100;

    // 运行时常量池（方法区的一部分）
    public static final String CONSTANT = "Hello";

    // JIT 编译后的机器码也缓存在方法区
    public void doSomething() { }
}
```

> 💡 **调优参数：** `-XX:MetaspaceSize=256m -XX:MaxMetaspaceSize=512m` 控制元空间大小。实际使用中元空间自动增长，但如果持续增长说明有类加载器泄漏。

### 10.3.4 程序计数器（PC Register）

- 每个线程私有，记录当前线程执行的**字节码行号**
- 执行 `native` 方法时，计数器值为 undefined
- **唯一不会发生 `OutOfMemoryError` 的区域**

### 10.3.5 本地方法栈（Native Method Stack）

与虚拟机栈类似，但为 **Native 方法**（通常用 C/C++ 编写）服务。HotSpot JVM 将两者合二为一。

---

## 10.4 垃圾回收算法

### 10.4.1 判断对象是否存活的算法

#### 引用计数法（Reference Counting）

每个对象有一个引用计数器，引用+1，引用失效-1。计数为0则回收。

**缺点：** 无法处理循环引用的情况。

```java
// 循环引用示例：refCount 无法归零
Object a = new Object(); // a.refCount = 1
Object b = new Object(); // b.refCount = 1
a.ref = b;               // b.refCount = 2
b.ref = a;              // a.refCount = 2
a = null;               // a.refCount = 1（不是0！）
b = null;               // b.refCount = 1（不是0！）
// a 和 b 实际上已经不可达，但引用计数不为0
// 引用计数法无法回收 → 主流 JVM 不使用
```

#### 可达性分析算法（Reachability Analysis）

从 **GC Roots** 出发，向下搜索，走过的路径称为**引用链**。不在引用链中的对象即不可达，可回收。

**GC Roots 包含：**

```
1. 虚拟机栈（栈帧中的局部变量表）中引用的对象
2. 方法区中类静态属性引用的对象
3. 方法区中常量引用的对象
4. 本地方法栈中 JNI 引用的对象
5. JVM 内部引用（ClassLoader、Long-lived 对象等）
6. 被同步锁（synchronized）持有的对象
7. 反映 JVM 内部情况的 JMX Bean、回调方法等
```

### 10.4.2 垃圾回收算法

#### 1. 标记-清除算法（Mark-Sweep）

**两步：** 1）标记所有存活对象；2）清除所有未标记对象。

```
标记前: [obj][obj][空][obj][空][空][obj]
标记中: 存活→标记    死亡→不标记
清除后: [obj][obj][  ][  ][  ][obj][  ]
         保留        清除（留下空洞）
```

**缺点：**
- **效率不稳定**：标记和清除都需要遍历全部对象，对象多时效率下降
- **产生内存碎片**：清除后内存不连续，大对象分配困难

#### 2. 复制算法（Copying）

将内存分成两块，每次只使用一块。GC 时将存活对象复制到另一块，然后一次性清理原区域。

```
┌─────────────┐         ┌─────────────┐
│    From     │  copy   │     To      │
│ [A][B][C][D]│ ──────→ │ [A][B][C]   │  D 是垃圾
└─────────────┘         └─────────────┘
```

**优点：** 没有内存碎片
**缺点：** 可用内存减半，浪费严重

> 💡 **实战应用：** 主流 JVM 的新生代就使用复制算法。由于新生代对象 98% 都是朝生夕死的，所以用 From Survivor 和 To Survivor 两个区域，每次 GC 将 Eden 和 From Survivor 中存活的对象复制到 To Survivor，然后清理。HotSpot 默认 Eden:Survivor = 8:1。

#### 3. 标记-整理算法（Mark-Compact）

**两步：** 1）标记存活对象；2）整理（Compact）存活对象，使它们向一端移动，然后清理边界外的内存。

```
整理前: [A][空][B][C][空][空][D]
整理后: [A][B][C][D][空][空][空]
         ←── 移动到一端 ──→
```

**优点：** 无内存碎片，不需要额外空间
**缺点：** 需要移动大量存活对象，整理阶段开销较大

> 💡 **实战应用：** 老年代使用标记-整理算法（CMS 收集器例外，使用标记-清除+并发清理）。

#### 4. 分代收集算法（Generational Collection）

根据对象存活周期将内存划分为新生代和老年代，分别采用最合适的算法。

```
┌─────────────────────────────────────┐
│                堆                    │
│  新生代 (Young Gen)  │  老年代 (Old)  │
│  ┌─────┬─────┬─────┐ │              │
│  │Eden │ S0  │ S1  │ │              │
│  └──┬──┴──┬──┴──┬──┘ │              │
│     │     │     │    │              │
│  复制算法 │  复制算法 │  标记整理算法  │
│  Minor GC │  Minor GC │  Major/Full GC│
└─────────────────────────────────────┘
```

**分代回收策略：**

| 区域 | 对象特点 | GC 类型 | 使用算法 |
|------|---------|---------|---------|
| 新生代 | 大多数对象朝生夕死 | Minor GC | 复制算法 |
| 老年代 | 存活时间长 | Major/Full GC | 标记-整理算法 |

**对象晋升规则：**

- 对象在 Eden 区出生
- Minor GC 后存活，进入 Survivor 区
- 年龄计数器 +1，当年龄 ≥ **15**（`-XX:MaxTenuringThreshold` 可调，默认 15）时，晋升老年代
- 大对象（`-XX:PretenureSizeThreshold`，默认 0 表示不启用）直接进入老年代

---

## 10.5 垃圾收集器

### 10.5.1 七种垃圾收集器总览

```
┌───────────────────────────────────────────────────────────┐
│                     新生代收集器                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ Serial   │  │ ParNew    │  │ Parallel │                │
│  │ (单线程)  │  │ (并行)    │  │ Scavenge │                │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                │
└───────┼────────────┼────────────┼─────────────────────────┘
        │            │            │
        │        ┌───▼────────────▼───┐
        │        │    CMS / Serial Old │
        │        │    (老年代并发)     │
        │        └─────────┬──────────┘
        │                  │
        │         ┌───────▼────────┐
        │         │ G1 / ZGC /    │
        │         │ Shenandoah     │
        │         │ (Region 化)    │
        │         └────────────────┘
```

### 10.5.2 各收集器详解

#### 1. Serial 收集器

**最基础、历史最悠久的单线程收集器。**

- 工作在新生代，使用**复制算法**
- Stop-The-World（STW），暂停所有用户线程
- 简单高效，没有线程切换开销

```bash
# 启用
-XX:+UseSerialGC
```

> 💡 **适用场景：** 客户端（Client）模式、内存几百 MB、单核机器。Serial Old 是 Serial 的老年代版本，使用标记-整理算法。

#### 2. ParNew 收集器

Serial 的多线程版本，**并行**收集新生代。

```bash
# 启用（CMS 的默认新生代收集器）
-XX:+UseParNewGC
```

- 多线程并行，GC 暂停时间比 Serial 短
- 在多核服务器上效果显著
- **可与 CMS 配合使用**

#### 3. Parallel Scavenge 收集器

**并行**收集新生代，关注点是**吞吐量（Throughput）**。

```
吞吐量 = 运行用户代码时间 / (运行用户代码时间 + GC 时间)
```

```bash
# 启用
-XX:+UseParallelGC
# 设置目标吞吐量（默认 99，即 99%）
-XX:GCTimeRatio=N
# 设置最大 GC 暂停时间（毫秒）
-XX:MaxGCPauseMillis=N
```

> 💡 **适合后台计算任务**，追求高吞吐量而非低延迟。

#### 4. Serial Old 收集器

Serial 的老年代版本，使用**标记-整理算法**，单线程。

#### 5. CMS 收集器（Concurrent Mark Sweep）

**老年代**收集器，追求**最短停顿时间**。

```
初始标记 (Initial Mark)     → STW，标记 GC Roots 直接引用的对象
并发标记 (Concurrent Mark)  → 不STW，沿着引用链追踪
重新标记 (Remark)           → STW，修正并发标记期间产生的变化
并发清除 (Concurrent Sweep) → 不STW，清除垃圾
```

**CMS 的四个阶段：**

| 阶段 | 是否 STW | 耗时 | 说明 |
|------|---------|------|------|
| 初始标记 | ✅ | 短 | 只标记 GC Roots 直接引用 |
| 并发标记 | ❌ | 长 | 耗时最长，不 STW |
| 重新标记 | ✅ | 较短 | 修正并发期间变化 |
| 并发清除 | ❌ | 长 | 不 STW |

```bash
# 启用
-XX:+UseConcMarkSweepGC
```

**CMS 的问题：**

- **CPU 敏感**：并发阶段占用 CPU，导致应用变慢
- **产生浮动垃圾**：并发清理阶段产生的垃圾只能等下次 GC
- **内存碎片**：使用标记-清除，不带整理，会产生碎片

```bash
# 解决内存碎片：-XX:+UseCMSCompactAtFullCollection
# 多次 Full GC 后进行一次整理：-XX:CMSFullGCsBeforeCompaction=N
```

> ⚠️ **JDK 14 已废弃 CMS**，官方建议使用 G1。

#### 6. G1 收集器（Garbage First）

**JDK 9+ 的默认收集器**，面向服务端应用的现代收集器。

**核心思想：** 将堆划分为多个大小相等的 **Region**（1MB~32MB），每个 Region 可以独立作为 Eden、Survivor 或老年代。

```
┌─────────────────────────────────────────┐
│  G1 Heap (2048 个 Region，每个 1MB)        │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐    │
│  │ Eden │ │ Eden │ │  S   │ │ Old  │    │
│  ├──────┤ ├──────┤ ├──────┤ ├──────┤    │
│  │ Old  │ │ Eden │ │ Old  │ │ Eden │    │
│  ├──────┤ ├──────┤ ├──────┤ ├──────┤    │
│  │  S   │ │ Old  │ │ Eden │ │  S   │    │
│  └──────┘ └──────┘ └──────┘ └──────┘    │
│   R1      R2       R3       R4          │
└─────────────────────────────────────────┘
```

**G1 的工作流程：**

1. **Young GC**：回收年轻代的 Region，将存活对象移至 Survivor 区或晋升到 Old 区
2. **Mixed GC**：老年代占比超过阈值时触发，回收所有年轻代 + 选定的部分老年代 Region
3. **Full GC**（G1 内部）：对象分配速率超过回收速率时触发（不应该发生）

**G1 的优势：**

- **可预测的停顿时间**：`-XX:MaxGCPauseMillis=200`（默认 200ms）
- **无内存碎片**：Region 内部复制，跨 Region 整理
- **大对象处理**：超过一个 Region 大小的对象叫 Humongous 对象，存入连续 Humongous Region

```bash
# 启用 G1
-XX:+UseG1GC

# 设置目标停顿时间
-XX:MaxGCPauseMillis=200

# 设置 Region 大小（1MB~32MB，必须是 2 的幂）
-XX:G1HeapRegionSize=4m

# 老年代达到此比例时触发 Mixed GC
-XX:InitiatingHeapOccupancyPercent=45
```

> 💡 **实战建议：** 对于要求低延迟的服务（如 Web 应用、交易系统），G1 是首选。对于超大堆（>64GB）且要求极低停顿（<10ms），考虑 ZGC。

#### 7. ZGC（Z Garbage Collector）

**JDK 11+ 支持**，目标是**极低停顿时间（<10ms）**，支持 **TB 级堆**。

- **染色指针（Colored Pointers）**：在指针上标记对象状态，不需要 STW 就能并发操作
- **读屏障（Load Barrier）**：读取引用时做轻微检查
- **并发操作**：几乎全部并发执行，只有短暂的 STW（用于根节点扫描）

```bash
# 启用 ZGC（JDK 15+ 完全生产就绪）
-XX:+UseZGC

# 设置堆大小
-Xmx16g -Xms16g

# 设置并发 GC 线程数
-XX:ConcGCThreads=N
```

> 💡 **ZGC vs G1 对比：**
> - G1：停顿时间可预测，但无法保证 <10ms
> - ZGC：停顿时间 <10ms，支持超大堆，但 CPU 开销略高
> - G1 适合 GB 级别堆，ZGC 适合 TB 级别堆

#### 8. Shenandoah（OpenJDK 集成）

与 ZGC 类似，**非 Oracle 官方**（Red Hat 开发，后进入 OpenJDK）。停顿时间不依赖堆大小。

```bash
-XX:+UseShenandoahGC
```

### 10.5.3 七种收集器对比

| 收集器 | 作用区域 | 算法 | 并发 | 停顿时间 | JDK 版本 |
|--------|---------|------|------|---------|---------|
| Serial | 新生代 | 复制 | 单线程 | 较长 | 1.0+ |
| Serial Old | 老年代 | 标记-整理 | 单线程 | 较长 | 1.0+ |
| ParNew | 新生代 | 复制 | 多线程 | 较短 | 1.4+ |
| Parallel Scavenge | 新生代 | 复制 | 多线程 | 可配置吞吐量 | 1.4+ |
| CMS | 老年代 | 标记-清除 | 并发 | 较短（并发） | 1.5+，**JDK 14 废弃** |
| G1 | 新生代+老年代 | 标记-整理+复制 | 并发 | 可预测 | JDK 7+，**JDK 9 默认** |
| ZGC | 新生代+老年代 | 标记-整理+染色指针 | 并发 | <10ms | JDK 11+ |
| Shenandoah | 新生代+老年代 | 标记-整理+染色指针 | 并发 | <10ms | JDK 12+ |

---

## 10.6 JVM 调优与常用命令

### 10.6.1 核心调优参数

#### 堆内存参数

```bash
# 初始堆大小 / 最大堆大小
-Xms256m          # 初始堆大小
-Xmx1024m         # 最大堆大小
-Xmn128m          # 新生代大小（不含永久代/元空间）
-Xms512m -Xmx512m  # 生产环境建议相同，避免动态调整

# 新生代比例（设置 NewRatio 就不要单独设 NewSize/MaxNewSize）
-XX:NewRatio=2        # 新生代:老年代 = 1:2（默认）
-XX:SurvivorRatio=8   # Eden:Survivor = 8:1:1（默认）

# 大对象直接进入老年代
-XX:PretenureSizeThreshold=10m   # 超过 10MB 的对象直接进老年代

# 对象晋升年龄
-XX:MaxTenuringThreshold=15      # 默认 15，最大可设 15
```

#### 元空间参数

```bash
# 元空间大小（不再占用堆）
-XX:MetaspaceSize=256m    # 初始元空间大小
-XX:MaxMetaspaceSize=512m # 最大元空间大小
```

#### GC 参数

```bash
# 选择垃圾收集器
-XX:+UseSerialGC           # Serial + Serial Old
-XX:+UseParallelGC         # Parallel Scavenge + Serial Old
-XX:+UseParallelOldGC      # Parallel Scavenge + Parallel Old
-XX:+UseParNewGC           # ParNew + Serial Old（CMS 新生代）
-XX:+UseConcMarkSweepGC    # ParNew + CMS（已废弃）
-XX:+UseG1GC               # G1（推荐）
-XX:+UseZGC                # ZGC
-XX:+UseShenandoahGC       # Shenandoah

# Parallel Scavenge 吞吐量设置
-XX:GCTimeRatio=99         # 吞吐量目标 = 99%
-XX:MaxGCPauseMillis=200   # 最大 GC 暂停时间目标

# G1 特殊参数
-XX:MaxGCPauseMillis=200   # G1 目标停顿时间
-XX:G1HeapRegionSize=4m    # Region 大小
-XX:InitiatingHeapOccupancyPercent=45  # 老年代比例阈值
```

#### 其他常用参数

```bash
# 线程栈大小
-Xss256k    # 每线程栈大小，默认 1MB，生产环境可设小

# OOM 时生成堆转储
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/heapdump.hprof

# 输出 GC 日志
-Xlog:gc*:file=/var/log/gc.log:time,uptime,level,tags
# 或老格式
-XX:+PrintGCDetails -XX:+PrintGCTimeStamps -Xloggc:/var/log/gc.log
```

### 10.6.2 jmap — 内存映象工具

```bash
# 查看堆内存使用概况
jmap -heap <pid>

# 查看对象统计（哪些类占用最多）
jmap -histo <pid>
# 输出示例：
#  num     #instances         #bytes  class name
#  1:         12345        2048000  [Ljava.lang.Object;
#  2:          8900        1234567  java.lang.String
#  3:          5600         890000  com.example.MyClass

# 导出堆转储文件（用于 MAT / JProfiler 分析）
jmap -dump:format=b,file=heapdump.hprof <pid>

# 注意：生产环境导出大堆可能卡顿，建议用
jmap -dump:format=b,file=heapdump.hprof,live <pid>
# live 只保留存活对象，减小文件
```

**jmap -heap 输出示例：**

```
using thread-local object allocation.
Parallel GC with 4 thread(s)

Heap Configuration:
   MinHeapFreeRatio         = 0
   MaxHeapFreeRatio         = 100
   MaxHeapSize              = 1073741824 (1024.0MB)
   NewSize                  = 268435456 (256.0MB)
   MaxNewSize               = 268435456 (256.0MB)
   OldSize                  = 805306368 (768.0MB)
   NewRatio                 = 2
   SurvivorRatio            = 8
   MetaspaceSize            = 22020096 (21.0MB)
   CompressedClassSpaceSize = 1073741824 (1024.0MB)

Heap Usage:
   New Generation (Eden + 2 Survivor Space):
      capacity = 241172480 (230.0MB)
      used     = 12345678  (11.7MB)
      free     = 228826802 (218.3MB)
   79.13% used
```

### 10.6.3 jstat — 统计信息监控

```bash
# 查看 GC 统计（每 1000ms 刷新一次，共 10 次）
jstat -gc <pid> 1000 10

# 输出列说明：
#  S0C    S1C    S0U    S1U    EC       EU        OC         OU       MC     MU    CCSC   CCSU   YGC     YGCT    FGC    FGCT     CGC    CGCT     GCT
# 4096.0 4096.0 0.0    2048.0 32768.0  12345.0   65536.0    12345.0   4864.0 4567.0 512.0  256.0    123    0.456     3    0.123    12    0.234   0.690

# S0C/S1C: Survivor0/1 容量(KB)
# S0U/S1U: Survivor0/1 已用(KB)
# EC/EU:   Eden 区容量/已用
# OC/OU:   Old 区容量/已用
# MC/MU:   Metaspace 容量/已用
# YGC/YGCT: Young GC 次数/总耗时
# FGC/FGCT: Full GC 次数/总耗时
# GCT:     总 GC 耗时

# 查看类加载统计
jstat -class <pid>

# 查看 JIT 编译统计
jstat -compiler <pid>
```

### 10.6.4 jinfo — 运行时配置查看

```bash
# 查看所有 JVM 参数
jinfo -flags <pid>

# 查看某个具体参数
jinfo -flag MaxHeapFreeRatio <pid>

# 动态修改（部分参数可在线调整）
jinfo -flag +PrintGCDetails <pid>   # 开启
jinfo -flag -PrintGCDetails <pid>   # 关闭

# 查看 Java 版本和 JVM 信息
jinfo -sysprops <pid>
```

### 10.6.5 jstack — 线程栈分析

```bash
# 打印线程堆栈
jstack <pid>

# 查找死锁
jstack -l <pid> | grep -A 10 "Found one Java-level deadlock"
```

**典型线程状态分析：**

```
"http-nio-8080-exec-10" #50 daemon prio=5 os_prio=0 tid=0x... 
   java.lang.Thread.State: RUNNABLE
   at com.example.MyService.process(MyService.java:45)
   at com.example.Controller.handle(Controller.java:30)
   ...

"GC task thread#0" #31 prio=5 os_prio=0 tid=0x... 
   java.lang.Thread.State: RUNNABLE
   at ParallelTask.run(ParallelTask.java:...)
```

### 10.6.6 Arthas — 阿里诊断工具

Arthas 是线上问题诊断利器，支持热更新、方法监控、线程分析等。

#### 常用命令

```bash
# 启动 Arthas
java -jar arthas-boot.jar <pid>

# 或直接 attach
java -jar arthas.jar <pid>
```

```bash
# 查看类加载信息
sc -d com.example.MyService
# 输出类的基本信息、加载器、实例数量

# 查看方法调用耗时
trace com.example.MyService process '#cost > 100'
# 追踪 process 方法，耗时超过 100ms 的调用

# 监控方法调用统计
monitor -c 5 com.example.MyService process
# 每 5 秒输出一次统计

# 查看对象实例
sc -f com.example.MyService

# 反编译类
jad com.example.MyService

# 热更新代码（不重启修复 bug）
redefine /path/to/new/Class.class
```

**Arthas Dashboard（实时面板）：**

```bash
# 输入 dashboard 命令，进入实时监控面板
# 显示：线程信息、内存信息、GC 信息、方法调用
```

**trace 命令深入：**

```bash
# 完整链路追踪，显示每个节点耗时
trace *ServiceImpl methodName -n 5 --skipJDKMethod false

# 输出：
# `---[thread: http-nio-8080-exec-1] 500ms
#     +---[30ms] com.example.Dao.query()  # sql耗时
#     +---[460ms] com.example.ThirdParty.call()  # 第三方调用耗时
```

**Arthas + OOM 分析示例：**

```bash
# 1. 查看哪个类加载最多
sc -d com.example | grep classLoader

# 2. 内存泄漏检测
heapdump /tmp/heap.hprof

# 3. 重新加载后对比
memory_diff /tmp/before.hprof /tmp/after.hprof
```

### 10.6.7 GC 日志分析

#### 开启 GC 日志

```bash
# JDK 9+ 推荐格式
java -Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=10,filesize=10M \
     -jar myapp.jar

# 或老格式（JDK 8 及之前）
java -XX:+PrintGCDetails \
     -XX:+PrintGCDateStamps \
     -Xloggc:/var/log/gc.log \
     -XX:+UseG1GC \
     -jar myapp.jar
```

#### GC 日志解读

**Minor GC（日志）：**

```
2024-01-15T10:23:45.123+0800: 123.456: [GC (Allocation Failure)
  PSYoungGen: 32768K->4096K(37888K)] 
  98304K->69632K(262144K), 0.0234567 secs]
  [Times: user=0.09 sys=0.01, real=0.02 secs]
```

- `Allocation Failure`：新生代空间不足
- `PSYoungGen: 32768K->4096K`：GC 前 32768K，GC 后 4096K
- `98304K->69632K`：堆总使用从 98MB 降到 69MB
- `[Times]`：user（CPU用户态）、sys（内核态）、real（实际）时间

**Full GC（日志）：**

```
2024-01-15T10:23:50.789+0800: 129.122: [Full GC (Ergonomics)
  [PSYoungGen: 4096K->0K(37888K)]
  [ParOldGen: 245760K->123456K(245760K)]
  249856K->123456K(524288K), [Metaspace: 56789K->56789K(0K)]
  0.567890 secs]
```

**GC 日志分析工具：**

| 工具 | 特点 |
|------|------|
| **GCEasy** | 在线工具，图形化，URL 上传 gc.log |
| **GCViewer** | 开源，本地运行 |
| **IBM PMAT** | 分析 IBM JVM，图形化 |
| **日志行数统计** | `grep "Full GC" gc.log | wc -l` 统计 Full GC 频率 |

### 10.6.8 内存泄漏与 OOM 分析

#### 内存泄漏（Memory Leak）

程序不再使用的对象无法被 GC 回收，通常是因为**无意识持有对象引用**。

**常见泄漏场景：**

```java
// 场景 1：静态集合类长期持有对象引用
public class LeakDemo {
    private static List<Object> cache = new ArrayList<>();

    public void add(Object obj) {
        cache.add(obj); // 不断添加，永不清理
    }
}

// 场景 2：未关闭的资源（连接、Stream）
public class BadExample {
    public void read() {
        Connection conn = DB.getConnection();
        // 没有 finally/try-with-resources 关闭
        // 网络断开后连接对象无法回收
    }
}

// 场景 3：监听器未注销
button.addActionListener(e -> doSomething());
// 对话框关闭后，button 仍被引用，listener 也无法释放

// 场景 4：ThreadLocal 未清理
ThreadLocal<Map> tl = new ThreadLocal<>();
tl.set(map);
// 线程池复用时，ThreadLocalMap 中的 map 无法清理
```

**最佳实践：**

```java
// 用 WeakHashMap 让 entry 可以被回收
private static Map<Key, Value> cache = new WeakHashMap<>();

// 用完手动清理 ThreadLocal
try {
    tl.set(value);
    // do work
} finally {
    tl.remove();
}

// 资源关闭用 try-with-resources
try (Connection conn = DB.getConnection();
     Statement stmt = conn.createStatement()) {
    // work
} // 自动关闭
```

#### OOM（OutOfMemoryError）类型

| 错误类型 | 原因 | 解决方案 |
|---------|------|---------|
| `java.lang.OutOfMemoryError: Java heap space` | 对象创建过多、内存泄漏 | 增加 `-Xmx`，用 MAT 找泄漏 |
| `java.lang.OutOfMemoryError: GC overhead limit exceeded` | GC 花费时间 >98% 但回收 <2% | 增加堆，或修复内存泄漏 |
| `java.lang.OutOfMemoryError: Metaspace` | 类加载过多（动态类生成） | 增加 `-XX:MaxMetaspaceSize` |
| `java.lang.OutOfMemoryError: Unable to create new native thread` | 线程创建过多 | 减少 `-Xss`，限制线程数 |
| `java.lang.OutOfMemoryError: Direct buffer memory` | NIO 直接内存泄漏 | 检查 `ByteBuffer.allocateDirect()` |

**OOM 实战分析步骤：**

```bash
# 1. 添加 OOM 时导出堆
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/heapdump.hprof

# 2. 重启应用后观察
# 3. 用 MAT 打开 .hprof 文件
#    - Histogram：按类统计实例数量
#    - Dominator Tree：找最大对象引用链
#    - Top Consumers：大对象分析

# 4. 用 Arthas 实时观察
dashboard      # 看哪个区域内存持续增长
heapdump       # 导出实时堆
```

---

## 10.7 常见面试题

### Q1：JVM 内存结构与 Java 内存模型（JMM）的区别？

**JVM 内存结构**是 JVM 运行时数据区的物理划分（堆、栈、方法区等）。**Java 内存模型（JMM）** 是 `java.util.concurrent` 的基础，定义了多线程间共享变量的可见性、有序性和原子性（主内存 vs 工作内存，`volatile`、`synchronized` 的语义）。

### Q2：对象的创建过程？

```
1. 检查类是否已加载（类加载）
   ↓
2. 在堆中分配内存（指针碰撞 / 空闲列表）
   ↓
3. 零值初始化（所有字段设默认值）
   ↓
4. 设置对象头（Mark Word、类型指针）
   ↓
5. 执行 <init> 构造函数
```

### Q3：双亲委派模型？有什么好处？

类加载器收到请求时先向上委派，最顶层父加载器无法处理才自己加载。好处：避免类的重复加载，防止核心 API 被篡改，保证安全性。

### Q4：什么情况下会触发 Full GC？

1. 老年代空间不足
2. `System.gc()` 调用（建议触发，不保证）
3. MetaSpace 满（CMS 回收时 MetaSpace 空间不足也会触发 Full GC）
4. Minor GC 前检查老年代放不下晋升对象，触发 PretenureSizeThreshold
5. 分配担保失败（Handle Promotion Failure）

### Q5：G1 和 ZGC 的区别？

| 维度 | G1 | ZGC |
|------|----|----|
| 停顿时间 | 可预测，但通常 >10ms | <10ms，停顿时间不依赖堆大小 |
| 堆大小 | 建议 <64GB | 支持 TB 级 |
| 算法 | Region+标记整理 | 染色指针+读屏障 |
| JDK 默认 | JDK 9+ | JDK 11+ |
| 成熟度 | 生产成熟 | JDK 15+ 完全生产 |

### Q6：Minor GC 和 Full GC 的区别？

| 维度 | Minor GC | Full GC |
|------|---------|---------|
| 触发区域 | 新生代 | 老年代 + 新生代 + 方法区 |
| 触发条件 | Eden 满 | 老年代满 / System.gc() / 分配担保失败 |
| STW 时间 | 短（毫秒级） | 长（几百毫秒~秒级） |
| 回收算法 | 复制 | 标记-整理/清除 |

### Q7：JVM 调优的一般思路？

```
1. 监控：jstat / Arthas dashboard / GC 日志
   ↓
2. 确定瓶颈：Minor GC 频繁？Full GC 频繁？对象分配过快？
   ↓
3. 针对性调优：
   - Minor GC 频繁 → 增大新生代 (-Xmn)
   - Full GC 频繁 → 分析是老年代还是 MetaSpace 问题
   - OOM → HeapDump 分析内存泄漏
   ↓
4. 验证：调整后持续观察 GC 曲线
```

### Q8：什么是 Stop-The-World（STW）？

GC 时，JVM 需要暂停所有应用线程（除 GC 线程外），这个暂停就是 STW。所有垃圾收集器都无法完全避免 STW，只能尽量缩短停顿时间。G1/ZGC 通过并发阶段将大部分工作与用户线程并行执行，减少 STW 时间。

---

## 本章小结

本章系统讲解了 JVM 的核心知识体系：

- **JVM 整体结构**：类加载子系统、执行引擎、运行时数据区，三者协同工作完成 Java 程序的运行
- **类加载机制**：加载→验证→准备→解析→初始化五步走，双亲委派模型保证了类的唯一性和安全性，SPI、Tomcat 等场景会主动打破委派
- **运行时数据区**：堆（对象实例）、栈（方法调用）、方法区（类元信息）、程序计数器（行号）、本地方法栈（Native），各有分工
- **垃圾回收算法**：引用计数 vs 可达性分析，标记-清除/复制/标记-整理/分代收集，各有适用场景
- **七种垃圾收集器**：从 Serial 到 ZGC，核心区别在于串行/并行/并发、停顿时间、吞吐量
- **调优实战**：jmap/jstat/jstack/Arthas 四大命令，加上 GC 日志分析，是定位生产问题的必备技能
- **内存泄漏与 OOM**：掌握常见泄漏模式、根因分析方法、Arthas+MAT 组合拳

> **面试高频关键词：** 双亲委派、Minor/Full GC、G1 vs ZGC、STW、内存泄漏、OOM 排查、JIT 编译、对象头（Mark Word）、TLAB。

---

**下一章：Ch11 - 网络编程**
