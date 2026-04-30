# 第9章 并发编程

## 摘要

> 本章系统讲解 Java 并发编程的核心知识，从基础的线程概念、生命周期出发，延伸至线程池的精细化配置，再到 JVM 层面的内存模型（JMM）与 synchronized/volatile 的底层机制；随后深入 JUC 并发工具箱——AQS、ReentrantLock、CountDownLatch、CyclicBarrier、Semaphore 的原理与实战用法；最后覆盖 LockSupport 的线程协作、ThreadLocal 的内存泄漏与扩容，以及线程池调优与高频面试题。全文配以完整代码示例，帮助读者建立从“会用”到“理解原理”再到“工程调优”的完整知识体系。

---

## 9.1 并发编程概述与基本概念

### 9.1.1 为什么要并发

- **充分利用多核 CPU**：现代服务器多为多核，单线程只能使用一个核心
- **提高程序吞吐量**：I/O 阻塞时，CPU 可以切换到其他任务
- **提升响应速度**：将耗时操作放在后台，不阻塞用户交互

> **并发（Concurrency）** 与 **并行（Parallelism）** 的区别：并发是多个任务交替执行（同一时刻只有一个任务运行，但切换速度快），并行是多个任务真正同时执行（需要多核 CPU）。

### 9.1.2 进程与线程

| 维度 | 进程（Process） | 线程（Thread） |
|------|----------------|----------------|
| 资源拥有 | 独立虚拟地址空间 | 共享进程资源 |
| 切换开销 | 大（需切换页表、寄存器） | 小（共享地址空间） |
| 通信方式 | 管道、Socket、共享内存 | 直接读写共享对象 |
| 独立性 | 完全隔离 | 共享堆内存 |

Java 程序运行在 JVM 上，JVM 本身是一个进程。默认情况下，JVM 启动至少包含：

- **主线程**（`main` 方法所在线程）
- **GC 线程**（垃圾回收）

### 9.1.3 并发编程中的核心问题

1. **可见性（Visibility）**：一个线程对共享变量的修改，其他线程能否立即看到
2. **有序性（Ordering）**：指令重排序是否导致结果不符合预期
3. **原子性（Atomicity）**：一组操作是否不可分割

这三个问题被统称为并发编程的"三要素"，也是后续所有解决方案的出发点。

---

## 9.2 线程基础（Thread、Runnable、Callable、Future）

### 9.2.1 Thread 类的生命周期与状态

Java 中线程使用 `java.lang.Thread` 表示，其生命周期由 `java.lang.Thread.State` 枚举定义：

```java
public enum State {
    NEW,         // 创建但未启动
    RUNNABLE,    // 可运行（包含就绪和运行中）
    BLOCKED,     // 阻塞（等待获取monitor锁）
    WAITING,     // 无限期等待（Object.wait / Thread.join / LockSupport.park）
    TIMED_WAITING, // 带超时的等待（Thread.sleep / Object.wait(timeout)）
    TERMINATED   // 已终止
}
```

**状态流转图：**

```
                    ┌─────────┐
                    │  NEW   │ ← new Thread()
                    └────┬────┘
                         │ start()
                         ▼
                 ┌───────────────┐
                 │   RUNNABLE     │ ← run() 执行中 / 就绪队列中
                 └───────┬───────┘
           ┌──────────────┼──────────────┐
           │              │              │
     join()/wait()   sleep()/       抢到锁
           │         parkNanos()       │
           ▼              ▼             ▼
      ┌─────────┐  ┌────────────┐  ┌──────────┐
      │ WAITING │  │TIMED_WAITING│  │ BLOCKED  │
      └────┬────┘  └──────┬─────┘  └────┬─────┘
           │             │              │
           └─────────────┴──────────────┘
                         │
                    重新进入 RUNNABLE
```

> **常见误区**：`Thread.sleep()` 不会释放锁，而 `Object.wait()` 会释放锁并进入等待队列。

### 9.2.2 创建线程的几种方式

#### 方式一：继承 Thread 类

```java
Thread t = new Thread() {
    @Override
    public void run() {
        System.out.println("Hello from " + Thread.currentThread().getName());
    }
};
t.start();
```

#### 方式二：实现 Runnable 接口（推荐）

```java
Runnable task = () -> System.out.println("Hello from " + Thread.currentThread().getName());
new Thread(task, "my-thread").start();
```

#### 方式三：实现 Callable 接口 + FutureTask

`Callable` 与 `Runnable` 的区别在于 `Callable` **有返回值**且**可以抛出受检异常**。

```java
Callable<Integer> callable = () -> {
    System.out.println("计算中...");
    Thread.sleep(1000);
    return 42;
};

FutureTask<Integer> futureTask = new FutureTask<>(callable);
new Thread(futureTask, "calc-thread").start();

// 阻塞等待结果
Integer result = futureTask.get();  // 会抛异常，需捕获
System.out.println("结果: " + result);
```

### 9.2.3 Future 详解

`Future` 代表一个异步计算的结果，提供以下核心方法：

| 方法 | 描述 |
|------|------|
| `get()` | 阻塞等待结果，支持超时重载 `get(timeout, unit)` |
| `cancel(boolean)` | 尝试取消任务 |
| `isDone()` | 判断任务是否完成 |
| `isCancelled()` | 判断任务是否被取消 |

**实战注意：** `get()` 是阻塞调用，如果在主线程调用且不设超时，可能导致主线程被长时间挂起。在实际项目中，建议使用带超时的版本：

```java
Integer result;
try {
    result = future.get(5, TimeUnit.SECONDS);
} catch (TimeoutException e) {
    future.cancel(true);
    System.out.println("任务超时，已取消");
} catch (ExecutionException e) {
    System.out.println("任务执行异常: " + e.getCause().getMessage());
}
```

### 9.2.4 线程的基本操作

```java
// 线程命名
Thread t = new Thread(task, "worker-1");

// 线程让步（让出CPU给同优先级线程，不保证一定切走）
Thread.yield();

// 线程休眠（不释放锁）
Thread.sleep(500);

// 线程加入（等待目标线程执行完毕）
t.join();              // 无限等待
t.join(2000);         // 最多等2秒

// 设置守护线程（JVM退出时不等待）
Thread daemon = new Thread(() -> {});
daemon.setDaemon(true);
daemon.start();

// 中断线程（协作式，非强制）
thread.interrupt();           // 设置中断标志
thread.isInterrupted();      // 查询中断标志
Thread.interrupted();        // 静态方法，清除中断标志并返回原值
```

> **重要**：`interrupt()` 只是设置中断标志，不会真正停止线程。正确的线程停止方式是让线程的 `run()` 方法自然结束，或者通过检查中断标志自行退出：
>
> ```java
> public class StoppableTask implements Runnable {
>     @Override
>     public void run() {
>         while (!Thread.currentThread().isInterrupted()) {
>             // 做事情...
>             try {
>                 // 阻塞方法会抛出 InterruptedException
>                 Thread.sleep(100);
>             } catch (InterruptedException e) {
>                 // 捕获后应退出，或重新设置中断标志
>                 Thread.currentThread().interrupt();
>                 break;
>             }
>         }
>     }
> }
> ```

---

## 9.3 线程池（7大参数、拒绝策略、4种类型、Executor家族）

### 9.3.1 为什么使用线程池

- **降低资源消耗**：避免反复创建/销毁线程的开销
- **提高响应速度**：任务到达时可直接复用已有线程
- **提高线程可管理性**：统一分配、调优、监控
- **提供更多功能**：定时执行、周期执行、并发控制

### 9.3.2 ThreadPoolExecutor 7大参数

```java
public ThreadPoolExecutor(
    int corePoolSize,              // 核心线程数
    int maximumPoolSize,           // 最大线程数
    long keepAliveTime,            // 空闲线程存活时间
    TimeUnit unit,                 // 时间单位
    BlockingQueue<Runnable> workQueue,  // 任务队列
    ThreadFactory threadFactory,   // 线程工厂
    RejectedExecutionHandler handler  // 拒绝策略
)
```

**线程数增减规则（非常重要）：**

```
任务提交
    │
    ▼
┌─────────────────────────────────────┐
│  运行中线程 < corePoolSize？          │
│    YES → 创建新核心线程处理任务        │
│    NO  → 任务进入 workQueue           │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  workQueue 已满？                    │
│    YES → 运行中线程 < maximumPoolSize │
│           YES → 创建非核心线程处理      │
│           NO  → 触发拒绝策略          │
└─────────────────────────────────────┘
```

**常见坑：** 如果 `workQueue` 使用无界队列（如 `LinkedBlockingQueue()` 不指定大小），则 `maximumPoolSize` 永远无法达到，线程数永远不会超过 `corePoolSize`。

### 9.3.3 4种内置线程池

| 类型 | 构造方式 | 特点 |
|------|---------|------|
| `FixedThreadPool` | `newFixedThreadPool(n)` | 核心=最大=n，队列无界 |
| `CachedThreadPool` | `newCachedThreadPool()` | 核心=0，最大=Integer.MAX_VALUE，60s回收 |
| `SingleThreadExecutor` | `newSingleThreadExecutor()` | 单线程，队列无界 |
| `ScheduledThreadPool` | `newScheduledThreadPool(n)` | 支持定时/周期任务 |

> **生产警告**：`Executors` 提供的这些快捷构造方法，大多使用无界队列，在高并发场景下可能导致 OOM（内存溢出）。**生产环境务必使用 `new ThreadPoolExecutor(...)` 显式指定参数。**

### 9.3.4 拒绝策略

当线程池和队列都满了，新的任务将被拒绝，`RejectedExecutionHandler` 决定如何处理：

| 策略 | 行为 |
|------|------|
| `AbortPolicy`（默认） | 抛出 `RejectedExecutionException` |
| `CallerRunsPolicy` | 由调用线程直接执行（即提交任务的线程） |
| `DiscardPolicy` | 直接丢弃任务，不抛异常 |
| `DiscardOldestPolicy` | 丢弃队列中最老的任务，再次尝试执行新任务 |

**自定义拒绝策略示例：**

```java
ThreadPoolExecutor executor = new ThreadPoolExecutor(
    4, 8, 60L, TimeUnit.SECONDS,
    new ArrayBlockingQueue<>(200),
    new ThreadFactoryBuilder().setNameFormat("pool-%d").build(),
    (r, pool) -> {
        // 记录日志
        log.error("线程池已满，拒绝任务");
        // 可以尝试持久化到磁盘等降级处理
        throw new RejectedExecutionException("Task rejected");
    }
);
```

### 9.3.5 线程工厂 ThreadFactory

默认的 `DefaultThreadFactory` 行为中规中矩，生产环境建议自定义：

```java
ThreadFactory factory = new ThreadFactory() {
    private final AtomicInteger count = new AtomicInteger(1);

    @Override
    public Thread newThread(Runnable r) {
        Thread t = new Thread(r, "my-pool-" + count.getAndIncrement());
        t.setDaemon(false);  // 建议设为非守护线程
        t.setPriority(Thread.NORM_PRIORITY);
        return t;
    }
};
```

使用 Google Guava 的 `ThreadFactoryBuilder` 更方便：

```java
ThreadFactory factory = new ThreadFactoryBuilder()
    .setNameFormat("biz-pool-%d")
    .setUncaughtExceptionHandler((t, e) -> log.error("线程异常", e))
    .build();
```

### 9.3.6 正确关闭线程池

```java
// 方法一：温柔关闭（等任务执行完，不阻塞新任务提交）
executor.shutdown();

// 方法二：强制关闭（中断所有线程）
executor.shutdownNow();

// 正确等待终止
if (!executor.awaitTermination(60, TimeUnit.SECONDS)) {
    executor.shutdownNow();  // 超时后再次强制关闭
}
```

### 9.3.7 提交任务的正确姿势

```java
// 提交 Runnable（无返回值）
executor.execute(() -> {
    // 任务逻辑
});

// 提交 Callable（有返回值）
Future<String> future = executor.submit(() -> {
    return "result";
});

// 批量提交
List<Callable<Result>> tasks = Arrays.asList(
    () -> task1(),
    () -> task2()
);
List<Future<Result>> futures = executor.invokeAll(tasks);  // 全部完成才返回
```

---

## 9.4 线程安全与同步（synchronized、volatile、JMM）

### 9.4.1 synchronized 基本用法

`synchronized` 是 Java 内置的互斥锁，可修饰：

1. **实例方法**（锁对象 this）
2. **静态方法**（锁 Class 对象）
3. **代码块**（锁指定对象）

```java
// 修饰实例方法 - 锁 this
public synchronized void increment() {
    count++;
}

// 修饰静态方法 - 锁 Class 对象
public static synchronized void staticIncrement() {
    staticCount++;
}

// 修饰代码块 - 锁指定对象
public void incrementWithBlock() {
    synchronized (this) {    // 或 synchronized (lock)
        count++;
    }
}
```

### 9.4.2 synchronized 原理（Monitor 机制）

`synchronized` 的实现依赖 **Monitor（监视器锁）**，每个对象都有一把隐式的 Monitor。

**字节码层面：**

```java
// 同步代码块
synchronized (obj) {
    count++;
}
```

对应字节码：
```
monitorenter   // 进入监视器，锁计数+1
  ...           // 同步块内容
monitorexit    // 退出监视器，锁计数-1（可能执行两次：正常退出+异常退出）
```

**方法层面：**
`synchronized` 方法在 `flags` 中有 `ACC_SYNCHRONIZED` 标志，不需要 `monitorenter/monitorexit`。

**锁升级过程（无锁 → 偏向锁 → 轻量级锁 → 重量级锁）：**

```
┌──────────────────────────────────────────────────────┐
│                  Mark Word（64bits）                  │
├──────────┬───────┬──────────────┬─────────────────────┤
│   无锁    │ 偏向锁 │    轻量级锁     │       重量级锁       │
├──────────┼───────┼──────────────┼─────────────────────┤
│ 无锁标记  │ 线程ID │  指向栈帧的指针  │  指向Monitor的指针    │
│  分代年龄 │  epoch │              │                     │
└──────────┴───────┴──────────────┴─────────────────────┘
```

| 锁状态 | 竞争程度 | 优点 | 缺点 |
|-------|---------|------|------|
| 偏向锁 | 只有一个线程 | 无需任何同步开销 | 多线程竞争时撤销代价高 |
| 轻量级锁 | 少量线程交替执行 | 非阻塞，自旋等待 | 自旋消耗CPU |
| 重量级锁 | 多线程竞争激烈 | 无自旋，OS挂起线程 | 用户态→内核态，开销大 |

> **结论**：平时说的 `synchronized` 慢，指的是**重量级锁**的场景。JDK6 之后的优化（锁消除、锁粗化、偏向锁、轻量级锁）已大幅改善性能，大多数场景不需要刻意回避 `synchronized`。

### 9.4.3 volatile 关键字

`volatile` 是轻量级的同步机制，保证两点：

1. **可见性**：写 `volatile` 变量后，会**立即刷新到主内存**，并使其他CPU缓存失效；读 `volatile` 变量直接从主内存读取
2. **有序性**：禁止指令重排序（插入内存屏障）

**适用场景：**

```java
// 场景一：状态标志
volatile boolean running = true;

void stop() {
    running = false;  // 另一个线程能看到这个修改
}

// 场景二：单例模式的double-check（配合synchronized）
class Singleton {
    private static volatile Singleton instance;

    public static Singleton getInstance() {
        if (instance == null) {                  // 第一次检查
            synchronized (Singleton.class) {
                if (instance == null) {          // 第二次检查
                    instance = new Singleton();  // volatile防止指令重排序
                }
            }
        }
        return instance;
    }
}
```

> **`instance = new Singleton()` 的指令重排序问题：**
> 正常顺序是：1. 分配内存 → 2. 调用构造方法 → 3. 赋值给引用
> 但编译器可能重排序为：1 → 3 → 2
> 另一线程可能在 3 之后、2 之前看到 `instance != null`，但对象还未构造完成。`volatile` 禁止了这个重排序。

### 9.4.4 JMM（Java Memory Model）

JMM 是 JVM 定义的内存模型，规定了线程与主内存之间的抽象关系：

```
┌─────────────────────────────────────────┐
│              Main Memory（主内存）          │
│   所有共享变量存储在这里（实例字段、静态字段）    │
└───────────────┬─────────────────────────┘
                │  read / write（每条指令）
                ▼
┌─────────────────────────────────────────┐
│  Thread A's Working Memory（工作内存）     │
│  Thread B's Working Memory              │
│   包含线程独享的寄存器、L1/L2/L3缓存       │
└─────────────────────────────────────────┘
```

**八种原子操作：**

| 操作 | 作用 |
|------|------|
| `lock/unlock` | 作用于主内存变量 |
| `read/write` | 主内存→工作内存 / 工作内存→主内存 |
| `load/store` | read后放入变量 / store后写入变量 |
| `use/assign` | 传递给执行引擎 / 执行引擎赋值给工作内存变量 |
| `regsterAssign` | 工作内存变量同步回主内存 |

### 9.4.5 happens-before 规则

`happens-before` 是 JMM 最核心的概念：**如果 A happens-before B，那么 A 的执行结果对 B 可见**。

> 这不是说 A 必须在 B 之前执行，而是说**内存可见性的保证**。

**常见 happens-before 规则：**

1. **程序顺序规则**：同一线程中，前面的操作 happens-before 后面的操作
2. **监视器锁规则**：解锁 happens-before 后续的加锁
3. **volatile 规则**：对 volatile 变量的写 happens-before 后续的读
4. **线程启动规则**：`Thread.start()` happens-before 被启动线程中的任何操作
5. **线程终止规则**：线程中所有操作 happens-before 其他线程检测到终止（如 `t.join()` 返回）
6. **传递性**：A happens-before B，B happens-before C → A happens-before C

---

## 9.5 JUC并发工具（AQS、ReentrantLock、CountDownLatch、CyclicBarrier、Semaphore）

### 9.5.1 AQS 原理（AbstractQueuedSynchronizer）

**AQS** 是 JUC 中大多数并发组件的基石，JDK1.5 由 Doug Lea 引入。

**核心结构：**

```
         ┌──────────────────────────────┐
         │         AQS                  │
         │  ┌──────────────────────┐   │
         │  │      state (volatile) │   │
         │  └──────────────────────┘   │
         │                              │
         │  CHL队列（FIFO双向队列）       │
         │  ┌────┐ ┌────┐ ┌────┐       │
         │  │Node│→│Node│→│Node│→ ...  │
         │  └────┘ └────┘ └────┘       │
         └──────────────────────────────┘
```

**两个核心概念：**

1. **`state`**：一个 `volatile int` 变量，表示资源的可用状态。不同实现类对它有不同的解读：
   - `ReentrantLock`：state=0 表示未占用，>0 表示重入次数
   - `CountDownLatch`：state=初始计数，=0 时 latch 打开
   - `Semaphore`：state=可用许可证数量

2. **FIFO 队列**：CLH 队列的变体，一个双向链表组成的等待队列，头节点是已获取资源的线程（或虚拟头节点），其余节点是等待获取资源的线程

**AQS 两种模式：**

- **独占模式（Exclusive）**：同一时刻只有一个线程能获取资源，如 `ReentrantLock`
- **共享模式（Share）**：多个线程可同时获取资源，如 `Semaphore`、`CountDownLatch`

**模板方法模式：** AQS 将同步器的行为抽象为模板方法，开发者只需重写指定方法：

```java
// 独占模式：尝试获取锁
protected boolean tryAcquire(int arg) {
    throw new UnsupportedOperationException();
}

// 独占模式：尝试释放锁
protected boolean tryRelease(int arg) {
    throw new UnsupportedOperationException();
}

// 共享模式：尝试获取资源
protected int tryAcquireShared(int arg) {
    throw new UnsupportedOperationException();
}

// 共享模式：尝试释放资源
protected boolean tryReleaseShared(int arg) {
    throw new UnsupportedOperationException();
}

// 是否处于独占模式
protected boolean isHeldExclusively() {
    throw new UnsupportedOperationException();
}
```

### 9.5.2 ReentrantLock

`ReentrantLock` 是可重入的独占锁，实现了 `Lock` 接口，比 `synchronized` 更灵活。

#### 公平锁 vs 非公平锁

```java
// 非公平锁（默认）
ReentrantLock unfairLock = new ReentrantLock();

// 公平锁
ReentrantLock fairLock = new ReentrantLock(true);

// 公平锁保证 FIFO，先等待的线程先获得锁
// 非公平锁允许"插队"，新来的线程可能直接抢锁
```

**公平锁 vs 非公平锁的选择：**

| 场景 | 建议 |
|------|------|
| 高并发、吞吐量优先 | 非公平锁（减少线程切换开销） |
| 响应公平性要求（如数据库连接池） | 公平锁 |
| 锁竞争激烈且任务时间长 | 公平锁（避免线程饥饿） |

#### 可重入机制

`ReentrantLock` 是可重入锁，同一个线程可以多次获取：

```java
ReentrantLock lock = new ReentrantLock();

void m1() {
    lock.lock();
    try {
        System.out.println("m1 获取锁");
        m2();  // 重入
    } finally {
        lock.unlock();
    }
}

void m2() {
    lock.lock();
    try {
        System.out.println("m2 获取锁");  // 同一个线程再次获取成功
    } finally {
        lock.unlock();
    }
}
```

#### ReentrantLock 对比 synchronized

| 特性 | ReentrantLock | synchronized |
|------|--------------|---------------|
| 等待可中断 | `lockInterruptibly()` 支持 | 不可中断 |
| 公平/非公平 | 可配置 | 非公平 |
| 绑定多个条件 | `newCondition()` 多个 | 只有一个 |
| 释放方式 | 必须在 finally 中 unlock | 自动释放 |
| 性能（JDK6+） | 接近 | 接近 |

**条件变量（Condition）：**

`synchronized` 配合 `Object.wait()/notify()` 使用，而 `ReentrantLock` 可以创建多个 `Condition`：

```java
ReentrantLock lock = new ReentrantLock();
Condition a = lock.newCondition();
Condition b = lock.newCondition();

void awaitA() throws InterruptedException {
    lock.lock();
    try {
        a.await();  // 等待条件A
    } finally {
        lock.unlock();
    }
}

void signalA() {
    lock.lock();
    try {
        a.signal();  // 唤醒等待条件A的线程
    } finally {
        lock.unlock();
    }
}
```

### 9.5.3 CountDownLatch

**倒计时门栓**：让一个或多个线程等待，直到其他线程完成一组操作。

**核心原理：** 内部使用 AQS 的共享模式，`state` 表示计数次数。

```java
// 使用场景：主线程等待所有子任务完成
public class TaskDemo {
    public static void main(String[] args) throws InterruptedException {
        int taskCount = 5;
        CountDownLatch latch = new CountDownLatch(taskCount);

        ExecutorService pool = Executors.newFixedThreadPool(taskCount);
        for (int i = 0; i < taskCount; i++) {
            final int taskId = i;
            pool.submit(() -> {
                try {
                    System.out.println("任务 " + taskId + " 执行中...");
                    Thread.sleep((long) (Math.random() * 1000));
                    System.out.println("任务 " + taskId + " 完成");
                } finally {
                    latch.countDown();  // 计数-1
                }
            });
        }

        latch.await(10, TimeUnit.SECONDS);  // 等待所有任务，最多等10秒
        System.out.println("所有任务完成，主线程继续");

        pool.shutdown();
    }
}
```

**常见坑：** `CountDownLatch` 是一次性的，计数到 0 后不能再重置。如果需要循环使用，用 `CyclicBarrier`。

### 9.5.4 CyclicBarrier

**循环栅栏**：让一组线程相互等待，直到所有人都到达屏障点后一起继续执行；之后屏障重置，可重复使用。

```java
// 使用场景：多线程分段计算，最后汇总
public class CyclicBarrierDemo {
    public static void main(String[] args) {
        int parties = 3;
        CyclicBarrier barrier = new CyclicBarrier(parties, () -> {
            // 所有线程到达后执行的汇总操作（可选）
            System.out.println(">>> 所有阶段完成，汇总结果");
        });

        ExecutorService pool = Executors.newFixedThreadPool(parties);
        for (int i = 0; i < parties; i++) {
            final int step = i + 1;
            pool.submit(() -> {
                try {
                    // 模拟分阶段任务
                    System.out.println("线程 [" + Thread.currentThread().getName() + "] 开始第" + step + "阶段");
                    Thread.sleep((long) (Math.random() * 1000));

                    System.out.println("线程 [" + Thread.currentThread().getName() + "] 到达屏障，等待其他人");
                    barrier.await();  // 等待所有人

                    System.out.println("线程 [" + Thread.currentThread().getName() + "] 继续执行第" + step + "阶段后续");
                } catch (InterruptedException | BrokenBarrierException e) {
                    e.printStackTrace();
                }
            });
        }

        pool.shutdown();
    }
}
```

**CountDownLatch vs CyclicBarrier：**

| 维度 | CountDownLatch | CyclicBarrier |
|------|---------------|---------------|
| 计数器 | 只减不重置 | 可循环重置 |
| 参与者 | 一组线程等待另一组线程 | 一组线程相互等待 |
| 完成后操作 | 不可定制 | 可在构造函数中传入汇总任务 |

### 9.5.5 Semaphore

**信号量**：控制同时访问特定资源的线程数量。

**原理：** 使用 AQS 共享模式，`state` 表示可用许可证数量。

```java
// 场景：限制数据库连接池最多10个并发连接
public class SemaphoreDemo {
    public static void main(String[] args) {
        Semaphore semaphore = new Semaphore(3);  // 3个许可证
        ExecutorService pool = Executors.newFixedThreadPool(10);

        for (int i = 0; i < 10; i++) {
            final int id = i;
            pool.submit(() -> {
                try {
                    semaphore.acquire();  // 获取许可证（阻塞直到可用）
                    System.out.println("线程 " + id + " 获取到许可证");
                    Thread.sleep(1000);   // 模拟使用资源
                    semaphore.release();  // 释放许可证
                    System.out.println("线程 " + id + " 释放许可证");
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            });
        }

        pool.shutdown();
    }
}
```

**Semaphore 的两种模式：**

```java
// 公平模式：按等待时间 FIFO 分配许可证
Semaphore fair = new Semaphore(3, true);

// 非公平模式（默认）：允许插队
Semaphore unfair = new Semaphore(3, false);
```

---

## 9.6 LockSupport 与线程协作

### 9.6.1 LockSupport 概述

`LockSupport` 是 JDK 并发包中最基础的线程阻塞/唤醒工具，是 `wait/notify`、`synchronized`、`Condition` 的底层依赖。

**核心 API：**

| 方法 | 描述 |
|------|------|
| `park()` | 阻塞当前线程（permit=0） |
| `park(Object blocker)` | 阻塞并记录阻塞对象（便于调试） |
| `unpark(Thread t)` | 唤醒指定线程（permit=1） |
| `parkNanos(long nanos)` | 阻塞指定纳秒 |
| `parkUntil(long deadline)` | 阻塞到指定时间点 |

### 9.6.2 park/unpark 原理

每个线程都有一个 `Parker` 对象，内含一个 `Counter`（permit 计数器）：

- `unpark()` → Counter=1，线程直接运行（不阻塞）
- `park()` → 检查 Counter：
  - 如果 Counter=1，则 Counter=0，线程继续运行（消费了 permit）
  - 如果 Counter=0，则线程阻塞等待

**与 wait/notify 对比：**

| 特性 | LockSupport.park/unpark | Object.wait/notify |
|------|------------------------|-------------------|
| 是否需要获取锁 | 不需要 | 必须持有对象锁 |
| 唤醒顺序 | unpark 先于 park 时，直接消费 permit | 不保证 |
| 可指定阻塞对象 | 可以（blocker 参数） | 不可以 |
| 中断响应 | 会立即返回（返回值为是否因中断唤醒） | 不响应中断 |

```java
// LockSupport 基础用法
Thread consumer = new Thread(() -> {
    System.out.println("消费者开始等待...");
    LockSupport.park();  // 阻塞
    System.out.println("消费者被唤醒，继续执行");
});
consumer.start();

Thread.sleep(2000);
System.out.println("生产者唤醒消费者");
LockSupport.unpark(consumer);
```

### 9.6.3 生产者-消费者模型实战

```java
import java.util.concurrent.locks.LockSupport;

public class ProducerConsumer {
    static Thread producer, consumer;

    public static void main(String[] args) {
        consumer = new Thread(() -> {
            System.out.println("消费者: 等待数据...");
            LockSupport.park();  // 等待数据
            System.out.println("消费者: 收到数据，进行处理");
        }, "consumer");
        consumer.start();

        producer = new Thread(() -> {
            System.out.println("生产者: 生产数据...");
            try { Thread.sleep(2000); } catch (InterruptedException e) {}
            System.out.println("生产者: 数据已就绪，唤醒消费者");
            LockSupport.unpark(consumer);
        }, "producer");
        producer.start();
    }
}
```

---

## 9.7 ThreadLocal（原理、内存泄漏、扩容机制）

### 9.7.1 ThreadLocal 基本用法

`ThreadLocal` 为每个线程提供独立的变量副本，实现线程隔离。

```java
// 场景：保存线程上下文（如用户ID、请求ID）
public class UserContext {
    private static final ThreadLocal<String> USER_ID = new ThreadLocal<>();

    public static void set(String userId) {
        USER_ID.set(userId);
    }

    public static String get() {
        return USER_ID.get();
    }

    public static void clear() {
        USER_ID.remove();  // 防止内存泄漏
    }
}

// 使用
public void process() {
    UserContext.set("user-123");
    try {
        String id = UserContext.get();  // 每个线程取到自己的值
        // ...
    } finally {
        UserContext.clear();
    }
}
```

### 9.7.2 ThreadLocal 原理

```
Thread
  └─ ThreadLocalMap (ThreadLocal的内部类)
        └─ Entry[] table
              └─ Entry (key=ThreadLocal, value=值)
```

- `Thread` 对象中有一个 `ThreadLocalMap`（`ThreadLocal` 的内部类）
- `ThreadLocalMap` 的 key 是**弱引用的 `ThreadLocal` 对象**，value 是强引用的实际值
- 每次 `get()`/`set()` 时，如果发现 key（ThreadLocal）已被 GC 回收，则清理该 Entry（**弱引用好处**）

### 9.7.3 内存泄漏分析与解决方案

**内存泄漏的原因（关键）：**

```
Entry结构：
  key: ThreadLocal<?> (WeakReference<ThreadLocal<?>>)
  value: Object (强引用)
```

正常情况：`ThreadLocal` 引用消失 → key 被 GC 回收 → `ThreadLocalMap.get()/set()` 时探测到 expunge stale entry → 清理 value

**危险场景：** `ThreadLocal` 不再使用，但**线程持续存活**（如线程池中的线程）：
- key 已回收（弱引用）
- value 仍然被 Entry 引用
- 线程不死，ThreadLocalMap 不死，value 内存泄漏

**最佳实践：**

```java
// 一定要在 finally 中 remove
try {
    UserContext.set(userId);
    // 业务逻辑
} finally {
    UserContext.remove();  // 显式清理
}
```

**如果不想每次都 try-finally**，可以用 `transmittable-thread-local` 库（TTL），它会自动在线程池任务提交前传递，任务结束后清理。

### 9.7.4 ThreadLocalMap 的扩容机制

`ThreadLocalMap` 的扩容发生在 `set()` 时：

- 初始容量：`INITIAL_CAPACITY = 16`
- 负载因子：`LOAD_FACTOR = 2/3`（即 0.666）
- 扩容阈值：`len * 2/3`（约 66% 时触发）

```java
private void resize() {
    Entry[] oldTab = table;
    int oldLen = oldTab.length;
    int newLen = oldLen * 2;  // 扩容为2倍
    Entry[] newTab = new Entry[newLen];
    // 重新 hash 放入新数组
}
```

**rehash 流程：**
1. `set()` 时，如果 size >= threshold，先尝试 `expungeStaleEntries()` 清理一次
2. 如果清理后 size 仍 >= threshold * 0.5，执行真正的 `resize()`

**实际扩容场景：** 如果大量 ThreadLocal 被使用（线程池线程 + 大量 ThreadLocal 实例），且没有及时 remove，可能触发扩容，导致内存占用增长。

### 9.7.5 ThreadLocal 常见踩坑点

```java
// 坑1：线程池中使用 ThreadLocal 不清理，导致数据串读
// ThreadPoolExecutor.runWorker() 不会清理 ThreadLocalMap
// 上一任务设置的用户ID，下一任务可能读到脏数据

// 坑2：子线程看不到父线程的 ThreadLocal
// ThreadLocal 是线程绑定的，子线程无法继承父线程的值
// 如需继承，使用 InheritableThreadLocal（但线程池场景仍有问题，需用 TTL）

// 坑3：InheritableThreadLocal 在线程池中的局限性
// InheritableThreadLocal 只在 Thread 构造时传递一次
// 线程复用时不更新，任务链中的数据可能过时
// 推荐使用 Alibaba 的 transmittable-thread-local (TTL)
```

---

## 9.8 线程池调优与面试题

### 9.8.1 核心线程数的计算

线程池大小设置是并发编程中最常见的调优点。公式选择取决于任务类型：

#### CPU 密集型任务

`CPU 密集型` = 纯计算任务，少 I/O（加解密、复杂运算、正则匹配）

```
最佳线程数 = CPU核心数 + 1
```

**原因：** CPU 密集型任务几乎 100% 占用 CPU，多出来的 1 个线程是防止缺页故障等导致的任务暂停。

```java
int cores = Runtime.getRuntime().availableProcessors();
int poolSize = cores + 1;  // 留一个备份
ExecutorService pool = new ThreadPoolExecutor(
    poolSize, poolSize, 0L, TimeUnit.MILLISECONDS,
    new LinkedBlockingQueue<>()
);
```

#### I/O 密集型任务

`I/O 密集型` = 涉及网络请求、数据库查询、文件读写的任务，CPU 大部分时间在等待 I/O 完成

```
最佳线程数 = CPU核心数 × (1 + (I/O耗时 / CPU耗时))
```

实践中通常使用经验值：

```
线程数 = CPU核心数 × 2    （保守）
线程数 = CPU核心数 × cpu倍增系数  （视 I/O 等待比例调整，通常 2-8 倍）
```

#### 混合型任务

如果任务同时包含 CPU 计算和 I/O 等待：

- 将 CPU 密集部分和 I/O 密集部分拆分，分别使用不同配置的线程池
- 或使用 `cores × 2` 作为起始值，通过压测调优

**通用实践：**

```java
int cores = Runtime.getRuntime().availableProcessors();

// CPU 密集：cores + 1
// I/O 密集：cores * 2 或更多（通过压测确定）
// 保守估计：cores * (1.5 ~ 2)

int cores = Runtime.getRuntime().availableProcessors();
int maxPoolSize = cores * 8;  // 经验值

ThreadPoolExecutor pool = new ThreadPoolExecutor(
    cores * 2,        // 核心线程数
    maxPoolSize,      // 最大线程数
    60L, TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(200),
    new ThreadFactoryBuilder().setNameFormat("biz-pool-%d").build(),
    new ThreadPoolExecutor.CallerRunsPolicy()
);
```

### 9.8.2 线程池参数动态调整

JDK9+ 提供 `Executorsors.newScheduledThreadPool()` 支持动态调整，但普通 `ThreadPoolExecutor` 不直接支持动态调整。可以通过反射或封装来调整：

```java
// 通过反射修改核心线程数
Field corePoolSizeField = ThreadPoolExecutor.class.getDeclaredField("corePoolSize");
corePoolSizeField.setAccessible(true);
corePoolSizeField.setInt(executor, newCoreSize);
```

或者使用第三方库如 Drools 的 `ResizableThreadPoolExecutor`、Guava 的 `ListeningExecutorService` 配合自定义实现。

### 9.8.3 线程池监控

生产环境务必添加监控：

```java
ThreadPoolExecutor executor = new ThreadPoolExecutor(4, 8, 60,
    TimeUnit.SECONDS, new ArrayBlockingQueue<>(100));

// 监控指标
public void monitor(ThreadPoolExecutor executor) {
    System.out.println("活跃线程数: " + executor.getActiveCount());
    System.out.println("队列大小: " + executor.getQueue().size());
    System.out.println("已完成任务数: " + executor.getCompletedTaskCount());
    System.out.println("总提交任务数: " + executor.getTaskCount());
    System.out.println("当前线程数: " + executor.getPoolSize());
}
```

### 9.8.4 高频面试题

**Q1：synchronized 和 ReentrantLock 的区别？**

| 特性 | synchronized | ReentrantLock |
|------|-------------|---------------|
| 锁类型 | 隐式锁（自动获取/释放） | 显式锁（手动 lock/unlock） |
| 公平性 | 非公平 | 可公平/非公平 |
| 等待可中断 | 否 | `lockInterruptibly()` |
| 条件变量 | 单一 | 多个 `newCondition()` |
| 锁检测 | 无法检测 | `isLocked()`, `isHeldByCurrentThread()` |
| 性能 | JDK6+ 优化后接近 | 接近 |

**Q2：volatile 和 synchronized 的区别？**

- `volatile` 只保证可见性和有序性，不保证原子性
- `synchronized` 保证原子性、可见性和有序性（互斥）
- `volatile` 不会阻塞，`synchronized` 会
- `volatile` 轻量，适用于状态标志等简单场景

**Q3：线程池的工作流程？**

见 9.3.2 的线程数增减规则图。重点回答：核心线程→队列→最大线程→拒绝策略的顺序，以及 maximumPoolSize 在无界队列下无效的原因。

**Q4：什么是 AQS？它是怎么工作的？**

AQS 是 JUC 并发组件的基石，通过一个 volatile 的 `state` 和一个 FIFO 队列管理线程的竞争。独占模式子类实现 `tryAcquire/tryRelease`，共享模式实现 `tryAcquireShared/tryReleaseShared`。线程获取资源失败时进入队列阻塞，获取成功时从队列移除。

**Q5：ThreadLocal 为什么会内存泄漏？怎么避免？**

ThreadLocalMap 的 Entry key 是弱引用，value 是强引用。当 ThreadLocal 不再被引用时，GC 回收 key，但 value 仍被 Entry 引用且无法清理（如果线程持续存活）。解决：每次使用完 `ThreadLocal` 后显式调用 `remove()`。

**Q6：为什么阿里巴巴代码规范禁止使用 `Executors.newFixedThreadPool` 等快捷方法创建线程池？**

这些方法使用无界队列（`LinkedBlockingQueue` 默认为 Integer.MAX_VALUE），在高并发下如果任务提交速度 > 处理速度，队列会无限堆积，最终导致 OOM。使用 `new ThreadPoolExecutor(...)` 并设置合理的队列大小和拒绝策略。

**Q7：什么是 happens-before？列举你知道的规则。**

happens-before 是 JMM 的核心概念，表示前一个操作的结果对后续操作可见。常见规则包括：程序顺序规则、监视器锁规则、volatile 规则、线程启动/终止规则、传递性等。JMM 通过这些规则，在不改变程序执行结果的前提下，放宽编译器和处理器的约束，实现性能优化。

**Q8：并发编程中的三大问题（可见性、有序性、原子性）产生的原因是什么？**

可见性：CPU 缓存导致各线程工作内存中共享变量副本不一致。有序性：编译器和 CPU 为了性能可能进行指令重排序。原子性：非原子操作在多线程环境下可能被其他线程打断。

---

## 本章小结

本章从 Java 并发编程的最小单元——线程出发，系统覆盖了以下内容：

- **线程基础**：`Thread` 的生命周期与状态、创建方式（Thread/Runnable/Callable/Future）、基本操作（sleep/yield/join/interrupt）
- **线程池**：`ThreadPoolExecutor` 7 大参数、4 种内置类型、4 种拒绝策略、正确关闭方式，以及为什么要避免使用 `Executors` 快捷方法
- **线程安全**：JMM 的内存抽象、`synchronized` 的 Monitor 机制与锁升级、`volatile` 的可见性+有序性保证、happens-before 规则
- **JUC 并发工具**：AQS 的 state+FIFO 队列核心原理、`ReentrantLock` 的公平/非公平/可重入、`Condition` 的条件变量、`CountDownLatch`/`CyclicBarrier`/`Semaphore` 的实战用法
- **LockSupport**：`park/unpark` 的 permit 机制，相比 `wait/notify` 的优势
- **ThreadLocal**：ThreadLocalMap 底层结构、弱引用 vs 强引用、内存泄漏原因与 `remove()` 最佳实践、扩容阈值与 rehash 机制
- **线程池调优**：CPU 密集型 vs I/O 密集型的核心线程数公式、监控指标、高频面试题解析

**核心记忆点：**

```
synchronized → 对象头Mark Word → Monitor → 锁升级（偏向→轻量→重量）
volatile     → 内存屏障 → 禁止重排序 + 保证可见性
AQS          → state + CLH队列 + 模板方法模式
ThreadLocal  → ThreadLocalMap（弱引用key）→ 每次用完必须remove()
线程池       → 核心线程满了→队列→最大线程→拒绝策略
```

---

**下一章：Ch10 - JVM虚拟机**
