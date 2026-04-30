# Ch08 - 集合进阶

## 本章概要

```
学习难度：★★★☆☆
重点程度：★★★★★
面试权重：★★★★★

本章前置知识：Ch04 集合框架基础
本章学习时间：约 4~6 小时

知识纵深：从接口契约 → 底层实现 → 并发安全 → 性能调优
适合人群：已掌握集合基础，欲深入理解实现原理与并发场景
```

---

本章在 Ch04 的基础上，对 Java 集合框架进行**进阶拓展**。重点聚焦于：

- **Map 家族**的深层实现：HashMap 源码解析、TreeMap 有序原理、LinkedHashMap 顺序机制、Hashtable 的历史包袱
- **Queue/Deque 体系**：阻塞 vs 非阻塞、优先级队列、延迟队列
- **并发集合**：ConcurrentHashMap 演进史（分段锁 → CAS + 红黑树）、CopyOnWriteArrayList、阻塞队列
- **fail-fast vs fail-safe**：两种迭代器失败机制的核心区别
- **选型指南与性能调优**：在不同业务场景下如何选对集合

---

## 8.1 集合框架回顾与分类

### 8.1.1 整体架构一览

Java 集合框架（JCF）分为两大根接口：

- **`Collection`**：单列元素集合
- **`Map`**：键值对（双列）集合

```
Collection
├── List（有序、可重复、有索引）
│   ├── ArrayList          ✅ 线程不安全
│   ├── LinkedList         ✅ 线程不安全
│   ├── Vector             ❌ 线程安全（synchronized）
│   └── Stack              ❌ 继承 Vector，落后
│
├── Set（无序、去重、无索引）
│   ├── HashSet            ✅ 基于 HashMap，线程不安全
│   ├── LinkedHashSet      ✅ 保持插入顺序
│   └── TreeSet            ✅ 基于 TreeMap，红黑树
│
└── Queue（队列，FIFO 为主）
    ├── LinkedList         ✅ 也实现了 Queue
    ├── PriorityQueue      ✅ 优先级队列（堆）
    ├── ArrayDeque         ✅ 比 LinkedList 效率更高
    └── BlockingQueue      ❌ 阻塞队列（并发）
        ├── LinkedBlockingQueue
        ├── ArrayBlockingQueue
        └── DelayQueue / SynchronousQueue ...

Map
├── HashMap                ✅ 线程不安全，最常用
├── LinkedHashMap          ✅ 保持插入顺序
├── TreeMap                ✅ 红黑树，key 有序
├── Hashtable              ❌ 全局锁，落后
├── ConcurrentHashMap      ❌ 线程安全，高并发首选
└── WeakHashMap / IdentityHashMap / EnumMap（特殊用途）
```

### 8.1.2 接口层级速查

| 接口 | 父接口 | 关键方法 |
|------|--------|---------|
| `List` | `Collection` | `get(int)`, `set(int, E)`, `add(int, E)`, `remove(int)` |
| `Set` | `Collection` | 与 Collection 一致（无新增） |
| `Queue` | `Collection` | `offer()`, `poll()`, `peek()` |
| `Deque` | `Queue` | `addFirst()`, `addLast()`, `pollFirst()`, `pollLast()` |
| `Map` | （根接口） | `get()`, `put()`, `keySet()`, `entrySet()` |

### 8.1.3 常见误区澄清

> **Map 不继承 Collection！** Map 是独立的根接口，这是一个经典面试题。
>
> `Map` 的 `keySet()` 返回的是 `Set`，`values()` 返回的是 `Collection`，`entrySet()` 返回的是 `Set<Entry<K,V>>`。

```java
// 常见错误：map.remove(collection) —— 编译不过
Map<String, Integer> map = new HashMap<>();
map.put("语文", 90);

// 正确做法：遍历匹配
map.entrySet().removeIf(entry -> entry.getValue() < 60);
```

---

## 8.2 Map 接口与实现类

### 8.2.1 HashMap（JDK8+）

#### 底层数据结构演进

| JDK 版本 | 底层结构 |
|---------|---------|
| JDK 7 | 数组 + 链表（Entry） |
| JDK 8+ | 数组 + 链表 + 红黑树（Node → TreeNode） |

> **为什么引入红黑树？**  
> 当哈希冲突严重、链表过长时，查找从 O(n) 退化为 O(n)。红黑树将最坏情况控制在 **O(log n)**。

#### 核心参数

```java
// 容量（capacity）：哈希表数组大小，必须是 2 的幂
// 默认初始容量：16
static final int DEFAULT_INITIAL_CAPACITY = 1 << 4;

// 最大容量：2^30
static final int MAXIMUM_CAPACITY = 1 << 30;

// 负载因子（loadFactor）：触发扩容的阈值比例
// 默认 0.75，表示 16 * 0.75 = 12 个元素时扩容
static final float DEFAULT_LOAD_FACTOR = 0.75f;

// 链表转红黑树的阈值（一个桶内节点数 >= 8）
static final int TREEIFY_THRESHOLD = 8;

// 红黑树转链表的阈值（一个桶内节点数 <= 6）
static final int UNTREEIFY_THRESHOLD = 6;

// 整个 HashMap 最小树形化容量阈值（数组长度 < 64 时优先扩容）
static final int MIN_TREEIFY_CAPACITY = 64;
```

#### 寻址机制（index 计算）

```java
// HashMap 通过 (n - 1) & hash 来确定元素落在哪个桶（bucket）
// 这就是为什么容量必须是 2 的幂 —— (n-1) 的二进制是全 1，& 操作等价于取模但更快
index = (n - 1) & hash

// hash() 方法：对 key 的 hashCode 再做一次扰动
static final int hash(Object key) {
    int h;
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
    // 高16位和低16位异或，降低碰撞概率
}
```

#### put 方法流程（JDK8）

```java
public V put(K key, V value) {
    return putVal(hash(key), key, value, false, true);
}

final V putVal(int hash, K key, V value, boolean onlyIfAbsent,
               boolean evict) {
    Node<K,V>[] tab; Node<K,V> p; int n, i;

    tab = table;
    if ((tab = table) == null || (n = tab.length) == 0)
        n = (tab = resize()).length;  // 懒初始化 + 首次扩容

    // 1. 计算桶位置，如果桶为空，直接新建节点
    if ((p = tab[i = (n - 1) & hash]) == null)
        tab[i] = newNode(hash, key, value, null);
    else {
        Node<K,V> e; K k;
        // 2. 桶中第一个节点 key 相同（hash相等且equals），覆盖
        if (p.hash == hash && ((k = p.key) == key || key.equals(k)))
            e = p;
        // 3. 已经是红黑树节点，调用树化插入
        else if (p instanceof TreeNode)
            e = ((TreeNode<K,V>) p).putTreeVal(this, tab, hash, key, value);
        // 4. 链表遍历
        else {
            for (int binCount = 0; ; ++binCount) {
                if ((e = p.next) == null) {
                    p.next = newNode(hash, key, value, null);
                    // 链表长度 >= 8，转红黑树
                    if (binCount >= TREEIFY_THRESHOLD - 1)
                        treeifyBin(tab, hash);
                    break;
                }
                if (e.hash == hash && ((k = e.key) == key || key.equals(k)))
                    break;
                p = e;
            }
        }
        // 5. key 已存在，覆盖 value
        if (e != null) {
            V oldValue = e.value;
            if (!onlyIfAbsent || oldValue == null)
                e.value = value;
            afterNodeAccess(e);
            return oldValue;
        }
    }
    ++modCount;
    if (++size > threshold)
        resize();  // 超过阈值，扩容
    afterNodeInsertion(evict);
    return null;
}
```

#### 扩容机制（resize）

```java
// 扩容前：capacity = 16，元素重新分布到 32 个桶
// 每个元素新的位置 = 原位置 OR 原位置 + 原容量（只有最高位是1的key会变）
// 即：要么在原桶，要么在原桶 + oldCap 的位置

// JDK7 中元素重排：每个节点重新计算 hash 并移动
// JDK8 优化：利用 (n-1) & hash 的特性，不需要重新计算 hash
//           只需要判断 hash & oldCap 的最高位是 0 还是 1 即可

// 示例：
// oldCap = 16 (10000b)
// key1: hash = 00011 -> 00011 & 10000 = 0 -> 原位置 3
// key2: hash = 10011 -> 10011 & 10000 = 1 -> 新位置 3+16 = 19
```

#### JDK7 vs JDK8 HashMap 核心区别

| 特性 | JDK 7 | JDK 8 |
|------|-------|-------|
| 底层结构 | 数组 + 链表 | 数组 + 链表 + 红黑树 |
| 插入方式 | 头插法 | 尾插法 |
| 扩容重排 | 全部重新计算 hash | 根据 hash & oldCap 判断新位置 |
| 死链问题 | 头插法可能产生环形链表（并发时） | 尾插法 + 红黑树，避免死链 |
| 查询复杂度 | 链表 O(n)，最坏 O(n) | 红黑树 O(log n)，最多退化到 O(n) |

> ⚠️ **并发陷阱：JDK7 扩容死链**  
> JDK7 使用头插法，并发扩容时链表顺序会反转。在 `transfer()` 方法中，如果两个线程同时扩容，可能形成环形链表，导致 `get()` 死循环。**JDK8 已修复（尾插法 + 红黑树）。** 但 HashMap 本身不是线程安全的，并发场景请用 `ConcurrentHashMap`。

#### 常见面试题：HashMap 为什么选用红黑树而非 AVL 树？

- AVL 树更平衡，查找更快（O(log n) 常数更小）
- 但 AVL 插入/删除时需要**更多旋转操作**来维持平衡
- HashMap 的 put 频率远高于 get，且数据量通常可控
- 红黑树的**插入开销更小**，且查找性能也能接受（最多两次旋转）

---

### 8.2.2 TreeMap

#### 核心特性

- 基于**红黑树**（Red-Black Tree）实现
- **key 必须可排序**（实现 `Comparable` 或传入 `Comparator`）
- **自然有序**或**自定义排序**
- 线程不安全

#### 基本操作

```java
// 方式1：自然排序（key 实现 Comparable）
TreeMap<String, Integer> map1 = new TreeMap<>();
map1.put("c", 3);
map1.put("a", 1);
map1.put("b", 2);
System.out.println(map1.keySet()); // [a, b, c] — 按字母顺序

// 方式2：自定义排序
TreeMap<Integer, String> map2 = new TreeMap<>(Comparator.reverseOrder());
map2.put(3, "三");
map2.put(1, "一");
map2.put(2, "二");
System.out.println(map2.keySet()); // [3, 2, 1] — 降序

// 方式3：自定义对象作为 key
TreeMap<Student, Integer> map3 = new TreeMap<>(new Comparator<Student>() {
    @Override
    public int compare(Student s1, Student s2) {
        return s1.getAge() - s2.getAge(); // 按年龄升序
    }
});

// 特有方法
map1.firstKey();           // 获取最小 key
map1.lastKey();            // 获取最大 key
map1.lowerKey("b");        // 获取严格小于 "b" 的最大 key
map1.higherKey("b");       // 获取严格大于 "b" 的最小 key
map1.subMap("a", "c");     // 获取 [a, c) 范围的子 Map
map1.headMap("b");         // 获取 key < "b" 的子 Map
map1.tailMap("b");         // 获取 key >= "b" 的子 Map
```

#### 典型应用场景

```java
// 场景1：排行榜，按分数排序
TreeMap<Integer, String> leaderboard = new TreeMap<>(Comparator.reverseOrder());
leaderboard.put(9500, "Alice");
leaderboard.put(8700, "Bob");
leaderboard.put(9800, "Charlie");

String topPlayer = leaderboard.firstEntry().getValue(); // Charlie

// 场景2：区间查询（分数在 600~800 之间的学生）
NavigableMap<Integer, String> range = leaderboard.subMap(600, 900);
// subMap 是原 Map 的视图，修改会影响原 Map
```

> ⚠️ **TreeMap 与 ConcurrentHashMap 的区别**：  
> TreeMap 保证 key 有序，但线程不安全；ConcurrentHashMap 线程安全但 key 无序。  
> 如果需要 key 有序且线程安全，使用 `ConcurrentSkipListMap`。

---

### 8.2.3 LinkedHashMap

#### 核心特性

- 继承 HashMap，内部维护**双向链表**记录插入顺序（accessOrder = false）
- 也支持**访问顺序**（accessOrder = true，用于 LRU 缓存）
- 线程不安全

#### 基本操作

```java
// 按插入顺序（默认）
LinkedHashMap<String, Integer> map = new LinkedHashMap<>();
map.put("语文", 90);
map.put("数学", 95);
map.put("英语", 88);
System.out.println(map.keySet()); // [语文, 数学, 英语] — 保持插入顺序

// 按访问顺序（LRU 缓存模式）
LinkedHashMap<String, Integer> lru = new LinkedHashMap<>(16, 0.75f, true);
lru.put("A", 1);
lru.put("B", 2);
lru.put("C", 3);
lru.get("A");  // 访问 A，将 A 移到链表尾部
lru.put("D", 4); // 插入 D，超出容量，删除最老的（链表头 = B）
System.out.println(lru.keySet()); // [C, A, D] — 注意 B 被淘汰了

// 限制容量（覆写 removeEldestEntry）
int MAX_ENTRIES = 3;
LinkedHashMap<String, Integer> cache = new LinkedHashMap<>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry eldest) {
        return size() > MAX_ENTRIES;
    }
};
```

#### 实现原理

```java
// LinkedHashMap 的节点继承了 HashMap.Node，并增加了前后指针
static class LinkedHashMapEntry<K,V> extends HashMap.Node<K,V> {
    LinkedHashMapEntry<K,V> before, after;  // 双向链表指针
}

// 按插入顺序遍历
// 重写了 newNode()，插入时自动维护链表顺序
// 重写了 iteration 方法（keySet()、values()、entrySet() 的迭代器）
```

> 💡 **LRU 缓存最佳实践**：  
> `LinkedHashMap(accessOrder=true)` + `removeEldestEntry` 是最简洁的 LRU 实现。  
> 但生产环境推荐使用 `ConcurrentHashMap` 或 `Guava Cache`，因为 `LinkedHashMap` 本身非线程安全。

---

### 8.2.4 Hashtable

#### 历史背景与现状

Hashtable 是 JDK 1.0 发布的早期实现，**已被弃用**。它的设计有严重的历史包袱：

```java
// Hashtable 特点：
// 1. key/value 都不能为 null（HashMap 可以有一个 null key）
// 2. 所有方法都 synchronized，线程安全但性能差
// 3. 扩容 2 倍 + 1（旧版本）
// 4. 枚举器是 "fail-fast"（抛出 ConcurrentModificationException）

Hashtable<String, Integer> table = new Hashtable<>();
table.put("A", 1);
// table.put(null, 1);  // NullPointerException！
// table.put("B", null); // NullPointerException！
```

#### Hashtable vs HashMap

| 特性 | Hashtable | HashMap |
|------|-----------|---------|
| 线程安全 | 是（全局锁） | 否 |
| 性能 | 差（锁粒度粗） | 好 |
| key/value null | 不允许 | 允许各一个 |
| 迭代器 | fail-fast | fail-fast |
| 初始容量 | 11 | 16 |
| 扩容策略 | 2n+1 | 2n |
| 同期新增 | Dictionary（已废弃） | Map 接口 |
| 推荐场景 | 无（应淘汰） | 几乎所有场景 |

> ⚠️ **Hashtable 的全表锁**：所有操作都锁住整个表，高并发下性能灾难。  
> 正确替代：`ConcurrentHashMap`。

---

### 8.2.5 Map 家族横向对比

| Map 实现 | 线程安全 | key 有序 | key 去重 | 底层结构 | 适用场景 |
|---------|---------|---------|---------|---------|---------|
| HashMap | ❌ | ❌ | ✅（hash+equals） | 数组+链表+红黑树 | 最常用，key 无序 |
| LinkedHashMap | ❌ | ✅（插入顺序/访问顺序） | ✅ | HashMap + 双向链表 | LRU 缓存、FIFO |
| TreeMap | ❌ | ✅（自然序/自定义） | ✅ | 红黑树 | 需要 key 排序 |
| Hashtable | ✅（全局锁） | ❌ | ✅ | 数组+链表 | 废弃，不用 |
| ConcurrentHashMap | ✅（桶锁/CAS） | ❌ | ✅ | 数组+链表+红黑树 | 高并发场景 |
| ConcurrentSkipListMap | ✅（跳表） | ✅（自然序） | ✅ | 跳表 | 高并发+有序 |
| WeakHashMap | ❌ | ❌ | ✅ | 数组+链表 | 缓存，key 无强引用时自动回收 |
| IdentityHashMap | ❌ | ❌ | ❌（==比较） | 数组 | 缓存/对象身份识别 |

---

## 8.3 Queue 与 Deque

### 8.3.1 Queue 接口

#### 核心方法对比

| 操作 | 抛出异常 | 返回特殊值 |
|------|---------|-----------|
| **入队**（队尾） | `add(e)` | `offer(e)` |
| **出队**（队首） | `remove()` | `poll()` |
| **查看队首** | `element()` | `peek()` |

> **原则**：
> - **非阻塞队列**：`offer()` / `poll()` / `peek()` 几乎总用这些（不抛异常）
> - **阻塞队列**：`put()` / `take()`（会阻塞）

```java
Queue<String> queue = new LinkedList<>();

queue.offer("A");  // 入队，返回 true
queue.offer("B");
queue.offer("C");

queue.poll();      // "A" — 取出并移除队首
queue.peek();      // "B" — 查看但不移除
queue.size();      // 2

// 模拟银行排队
Queue<Integer> waitingLine = new LinkedList<>();
waitingLine.offer(101);
waitingLine.offer(102);
waitingLine.poll();  // 101 先来先服务
```

---

### 8.3.2 Deque（双端队列）

Deque = Double Ended Queue，支持从**两端**入队和出队。

```java
Deque<String> deque = new ArrayDeque<>();

// 两端操作
deque.offerFirst("A");   // 头部入队
deque.offerLast("B");    // 尾部入队（等价于 offer）
deque.pollFirst();       // 头部出队
deque.pollLast();        // 尾部出队

// 用作栈（比 Stack 快）
Deque<Integer> stack = new ArrayDeque<>();
stack.push(1);           // 等价于 offerFirst
stack.push(2);
stack.pop();             // 2
stack.peek();            // 1

// 用作队列
Deque<String> q = new ArrayDeque<>();
q.offer("first");
q.offer("second");
q.poll();                // "first" — FIFO
```

> ⚠️ **为什么弃用 Stack？**  
> `Stack` 继承自 `Vector`（synchronized + 2倍扩容），性能差。  
> 用 `ArrayDeque` 替代，**效率高 3~4 倍**。  
> ```java
> // 废弃写法
> Stack<Integer> s = new Stack<>();
> // 推荐写法
> Deque<Integer> s = new ArrayDeque<>();
> ```

---

### 8.3.3 阻塞队列（BlockingQueue）

#### 核心接口

`BlockingQueue` 在 `Queue` 基础上增加了**阻塞等待**机制：

```java
public interface BlockingQueue<E> extends Queue<E> {
    // 队满时阻塞，直到有空位（或被中断）
    void put(E e) throws InterruptedException;

    // 队空时阻塞，直到有元素（或被中断）
    E take() throws InterruptedException;

    // 带超时阻塞
    boolean offer(E e, long timeout, TimeUnit unit) throws InterruptedException;
    E poll(long timeout, TimeUnit unit) throws InterruptedException;

    // 队列特性判断（非阻塞）
    int remainingCapacity();  // 剩余容量
}
```

#### JDK7 vs JDK8 对比：ArrayBlockingQueue vs LinkedBlockingQueue

| 特性 | ArrayBlockingQueue | LinkedBlockingQueue |
|------|-------------------|-------------------|
| 底层结构 | 有界数组（必须指定容量） | 无界链表（可指定容量， 默认 Integer.MAX_VALUE） |
| 锁机制 | **一把锁**（ReentrantLock） | **两把锁**（takeLock + putLock），入队出队可并发 |
| 吞吐量 | 较低 | 较高（业界性能首选） |
| 公平性 | 可选公平/非公平模式 | 非公平（无公平选项） |
| 内存分配 | 预分配数组，内存固定 | 按需分配节点，动态内存 |
| 空队列 take() | 阻塞 | 阻塞 |
| 满队列 put() | 阻塞 | 队列无界时不阻塞（除非指定容量） |

```java
// ArrayBlockingQueue — 有界，公平可配置
BlockingQueue<Integer> abq = new ArrayBlockingQueue<>(3, true); // 公平锁
abq.put(1);   // 队满则阻塞
abq.take();   // 队空则阻塞

// LinkedBlockingQueue — 推荐，高吞吐量
BlockingQueue<Integer> lbq = new LinkedBlockingQueue<>(100); // 可选容量
lbq.offer(1);
lbq.poll();

// 无界队列（无限膨胀风险）
BlockingQueue<Integer> unbounded = new LinkedBlockingQueue<>();
// 不指定容量时，默认 Integer.MAX_VALUE，put() 永不阻塞
```

#### 生产者-消费者模式实战

```java
public class ProducerConsumerDemo {
    public static void main(String[] args) {
        BlockingQueue<Integer> queue = new LinkedBlockingQueue<>(5);

        // 生产者
        Runnable producer = () -> {
            for (int i = 0; i < 20; i++) {
                try {
                    queue.put(i);  // 队满则阻塞
                    System.out.println("生产: " + i);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
        };

        // 消费者
        Runnable consumer = () -> {
            while (true) {
                try {
                    Integer val = queue.take();  // 队空则阻塞
                    System.out.println("消费: " + val);
                    Thread.sleep(500); // 模拟处理时间
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        };

        new Thread(producer, "生产者").start();
        new Thread(consumer, "消费者").start();
    }
}
```

#### 特殊阻塞队列

```java
// 1. SynchronousQueue — 不存储元素，每个 put 必须等一个 take，反之亦然
//    用途：零延迟传递，用于线程间直接交接
BlockingQueue<Integer> sq = new SynchronousQueue<>();
new Thread(() -> {
    try {
        sq.put(42); // 阻塞，直到另一个线程 take()
    } catch (InterruptedException e) {}
}).start();
sq.take(); // 立即拿到 42

// 2. DelayQueue — 元素必须实现 Delayed 接口，按延迟时间排序
//    用途：定时任务调度、订单超时取消、缓存过期
class DelayedTask implements Delayed {
    private final long delay;
    private final String task;

    public DelayedTask(long delay, String task) {
        this.delay = System.currentTimeMillis() + delay;
        this.task = task;
    }

    @Override
    public long getDelay(TimeUnit unit) {
        return delay - System.currentTimeMillis();
    }

    @Override
    public int compareTo(Delayed o) {
        return Long.compare(this.delay, ((DelayedTask) o).delay);
    }
}

// 使用
BlockingQueue<DelayedTask> dq = new DelayQueue<>();
dq.offer(new DelayedTask(3000, "3秒后执行"));
dq.offer(new DelayedTask(1000, "1秒后执行"));
dq.take(); // 1秒后返回 "1秒后执行"
dq.take(); // 再等2秒返回 "3秒后执行"

// 3. PriorityBlockingQueue — 无界优先级队列
//    底层是堆，队首是最小（或最大）元素，队空时 take() 阻塞
BlockingQueue<Integer> pbq = new PriorityBlockingQueue<>();
pbq.offer(5);
pbq.offer(2);
pbq.offer(8);
pbq.take(); // 2 — 按自然顺序弹出最小值
```

---

### 8.3.4 Queue 选型指南

| 场景 | 推荐实现 |
|------|---------|
| 普通 FIFO 队列 | `ArrayDeque`（比 LinkedList 快） |
| 线程安全 FIFO | `LinkedBlockingQueue` |
| 优先级调度 | `PriorityQueue` / `PriorityBlockingQueue` |
| 定时延迟任务 | `DelayQueue` |
| 线程间直接传递 | `SynchronousQueue` |
| 有界队列（高吞吐） | `LinkedBlockingQueue` |
| 有界队列（固定大小） | `ArrayBlockingQueue` |
| LIFO 栈 | `ArrayDeque`（不要用 Stack） |

---

## 8.4 ConcurrentHashMap

### 8.4.1 JDK7 分段锁（Segment）

#### 原理

JDK7 的 `ConcurrentHashMap` 采用了**分段锁**（Segment）设计：

```
ConcurrentHashMap
├── Segment[0] — 锁住部分桶
├── Segment[1] — 锁住部分桶
├── Segment[2] — 锁住部分桶
└── ...
```

- 整个 Map 被分为 **16 个 Segment**（可构造时指定，最大 65536）
- 每个 Segment 类似于一个小的 `HashMap`，有自己的数组
- **读写操作只需锁住对应的 Segment**，不同 Segment 可并发执行

```java
// JDK7 核心结构（简化）
public class ConcurrentHashMap<K, V> {
    final Segment<K, V>[] segments;

    public V put(K key, V value) {
        // 1. 计算 key 的 hash
        int hash = hash(key);
        // 2. 定位 Segment（下标）
        int segIdx = (hash >>> 28) & 15;  // 16 个段
        // 3. 获取 Segment 锁（ReentrantLock）
        Segment<K, V> s = segments[segIdx];
        s.lock();  // 加锁
        try {
            // 4. 在 Segment 内部执行 put（逻辑同 HashMap）
            return s.putValue(key, hash, value);
        } finally {
            s.unlock();
        }
    }

    public V get(K key) {
        // get 不加锁！用 volatile 保证可见性
        int hash = hash(key);
        Segment<K, V> s = segments[(hash >>> 28) & 15];
        return s.getValue(key, hash);
    }
}
```

#### 优点与局限

| 优点 | 局限 |
|------|------|
| 不同 Segment 可并发，最高达 16 倍并发 | 锁粒度仍然较粗（一个 Segment 包含多个桶） |
| get 不加锁，读性能好 | Segment 数量固定，无法动态扩展 |
| 线程安全 | key 跨 Segment 时无法保证原子性（如 `putAll`） |

---

### 8.4.2 JDK8+ CAS + Synchronized

JDK8 彻底抛弃了分段锁，改为更细粒度的**CAS + synchronized**：

```
不再分段锁 —— 锁住的是**单个桶**（bin），而非整个 Segment！
```

#### 核心数据结构

```java
// JDK8 Node 数组（类似 HashMap）
transient volatile Node<K, V>[] table;

// Node 结构（支持红黑树）
static class Node<K, V> implements Map.Entry<K, V> {
    final int hash;
    final K key;
    volatile V value;
    volatile Node<K, V> next;  // volatile 保证可见性
}
```

#### put 流程（JDK8）

```java
public V put(K key, V value) {
    return putVal(key, value, false);
}

final V putVal(K key, V value, boolean onlyIfAbsent) {
    if (key == null || value == null) throw new NullPointerException();
    int hash = spread(key.hashCode());
    int binCount = 0;

    for (Node<K, V>[] tab = table; ; ) {
        Node<K, V> f;
        int n, i, fh;

        // 1. 初始化表（CAS 保证只有一个线程初始化）
        if (tab == null || (n = tab.length) == 0)
            tab = initTable();

        // 2. 桶为空 —— CAS 尝试写入
        else if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
            if (casTabAt(tab, i, null, new Node<>(hash, key, value, null)))
                break;
        }
        // 3. 桶不为空，检测到扩容 —— 帮助扩容
        else if ((fh = f.hash) == MOVED)
            tab = helpTransfer(tab, f);
        // 4. 桶中有节点 —— synchronized 锁住该桶
        else {
            V oldVal = null;
            synchronized (f) {  // 锁住桶的第一个节点（头节点）
                if (tabAt(tab, i) == f) {
                    if (fh >= 0) {  // 普通链表
                        binCount = 1;
                        for (Node<K, V> e = f; ; ++binCount) {
                            if (e.hash == hash &&
                                ((k = e.key) == key || key.equals(k))) {
                                oldVal = e.value;
                                if (!onlyIfAbsent)
                                    e.value = value;
                                break;
                            }
                            Node<K, V> pred = e;
                            if ((e = e.next) == null) {
                                pred.next = new Node<>(hash, key, value, null);
                                break;
                            }
                        }
                    } else if (f instanceof TreeBin) {  // 红黑树
                        binCount = 2;
                        ((TreeBin<K, V>) f).putTreeVal(hash, key, value);
                    }
                }
            }

            if (binCount != 0) {
                if (binCount >= TREEIFY_THRESHOLD)
                    treeifyBin(tab, i);  // 链表转红黑树
                if (oldVal != null)
                    return oldVal;
                break;
            }
        }
    }
    addCount(1L, binCount);  // 计数 + 检查扩容
    return null;
}
```

#### 关键优化点

| 优化 | 说明 |
|------|------|
| **CAS 初始化** | `table == null` 时，多线程竞争通过 `CAS` 保证只有一个线程初始化 |
| **synchronized 只锁桶** | 锁粒度细化到单个桶（bin），而非整个 Map |
| **volatile 读** | `tabAt()` 通过 `Unsafe` 的 `getObjectVolatile` 保证可见性 |
| **扩容协助（helpTransfer）** | 检测到其他线程正在扩容时，帮助一起扩容，分担压力 |
| **红黑树** | 链表过长（>= 8）时树化，最坏查找 O(log n) |

#### CAS 操作详解（Unsafe）

```java
// 通过 Unsafe 直接操作内存，保证原子性
private static final Unsafe U = Unsafe.getUnsafe();

static final <K,V> Node<K,V> tabAt(Node<K,V>[] tab, int i) {
    return U.getObjectVolatile(tab, ((long)i << ASHIFT) + ABASE);
}

static final <K,V> boolean casTabAt(Node<K,V>[] tab, int i,
                                     Node<K,V> c, Node<K,V> v) {
    return U.compareAndSwapObject(tab, ((long)i << ASHIFT) + ABASE, c, v);
}
```

---

### 8.4.3 JDK7 vs JDK8 ConcurrentHashMap 对比

| 维度 | JDK 7 | JDK 8+ |
|------|-------|--------|
| 锁机制 | Segment 分段锁（ReentrantLock） | CAS + synchronized |
| 锁粒度 | Segment 级别（粗） | 桶级别（细） |
| 并发度 | 最多 16（Segment 数固定） | 理论上无上限（桶数量决定） |
| get 读操作 | 无锁（volatile） | 无锁（volatile） |
| put 写操作 | 锁 Segment | CAS（空桶）或 synchronized（桶已有节点） |
| 初始化 | 在构造函数中 | 懒初始化（首次 put 时） |
| 扩容 | 只能单线程扩容 | 多线程并发协助扩容（`helpTransfer`） |
| 红黑树 | 无 | 有（链表过长时树化） |
| 死链风险 | 无 | 无（synchronized + 尾插） |

---

### 8.4.4 扩容机制详解（JDK8）

#### 核心流程

```
触发条件：sizeCtl < 0（正在扩容）或 元素数量 > 阈值（capacity * loadFactor）

步骤：
1. 发现 table 正在被某个线程扩容（sizeCtl = -1）
2. 调用 helpTransfer()，协助扩容
3. 每个线程认领一段桶（transferIndex），并行迁移
4. 迁移完成后，table 指向新数组
```

```java
// sizeCtl 的语义：
// 正数：表示下次扩容的阈值（capacity * 0.75）
// -1  ：表示正在初始化
// -(1 + nThreads)：表示正在扩容，nThreads = -sizeCtl - 1

private final void transfer(Node<K, V>[] tab, Node<K, V>[] nextTab) {
    int n = tab.length, stride;

    // 每个线程最少认领 16 个桶（减少竞争）
    stride = (n >>> 3) / NCPU;  // 总共 n / 8 / CPU数
    if (stride < 16) stride = 16;

    // 初始化新数组（nextTab）
    if (nextTab == null) {
        nextTab = new Node[n << 1];  // 2 倍扩容
    }

    // transferIndex：从后往前分配桶区间
    for (int i = 0, bound = 0; ; ) {
        // ...
    }

    // 数据迁移（链表分化）
    // 与 HashMap 类似，hash & oldCap 判断新位置
    //   = 0 → 原位置
    //   = 1 → 原位置 + oldCap
}
```

#### 扩容时的读写

```java
// 读操作：始终读新表或旧表（volatile 保证）
Node<K,V>[] tab;
while ((tab = table) != null && (n = tab.length) > 0) {
    int index = (n - 1) & hash;
    Node<K,V> first = tabAt(tab, index);
    // ...
}

// 写操作：发现正在扩容，先 helpTransfer，再继续
if ((fh = f.hash) == MOVED)
    tab = helpTransfer(tab, f);
```

---

### 8.4.5 ConcurrentHashMap 常用操作

```java
ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();

// 基本操作
map.put("A", 1);
map.get("A");              // 1
map.remove("A");            // 返回被删除的值
map.size();                 // 元素个数（近似值，非精确）

// 原子操作（JDK8 新增）
map.putIfAbsent("B", 2);    // 仅当 key 不存在时才插入
map.replace("B", 2, 3);     // 仅当 oldValue 匹配时才替换
map.compute("C", (k, v) -> v == null ? 1 : v + 1); // 原子计算
map.merge("C", 1, Integer::sum); // 合并操作

// 批量操作（JDK8 新增）
map.forEach((k, v) -> System.out.println(k + "=" + v));
map.search(1, (k, v) -> v > 0 ? k : null);  // 搜索
map.reduce(1, (k, v) -> v, Integer::sum);  // 聚合

// ConcurrentHashMap 不支持 null key/value（防止歧义）
// map.put(null, 1);  // NullPointerException！
```

---

## 8.5 并发集合

### 8.5.1 CopyOnWriteArrayList

#### 核心思想

**写操作时复制整个数组**，读操作无需加锁。适用于**读多写少**的场景。

```java
// 底层结构
private volatile Object[] array;

public boolean add(E e) {
    final ReentrantLock lock = this.lock;
    lock.lock();
    try {
        Object[] elements = getArray();
        int len = elements.length;
        Object[] newElements = Arrays.copyOf(elements, len + 1);  // 复制
        newElements[len] = e;
        setArray(newElements);  // 原子替换引用（volatile）
        return true;
    } finally {
        lock.unlock();
    }
}

public E get(int index) {
    return get(getArray()[index]);  // 无锁读，volatile 保证可见性
}
```

#### 特性与局限

| 特性 | 说明 |
|------|------|
| 读写分离 | 写不影响读，读不加锁 |
| 最终一致性 | 写操作会创建副本 |
| 内存开销 | 每次写都复制数组，写频繁则内存压力大 |
| 迭代器 | fail-safe（不抛异常），但不保证最新数据 |

```java
CopyOnWriteArrayList<String> list = new CopyOnWriteArrayList<>();

list.add("A");
list.add("B");

// 迭代器（快照视角，copy-on-write时刻的数组）
Iterator<String> it = list.iterator();
list.add("C");  // 修改不影响已有迭代器
while (it.hasNext()) {
    System.out.println(it.next());  // 仍输出 A, B
}

// ⚠️ 典型陷阱：迭代器中不能执行写操作（UnsupportedOperationException）
// it.remove(); // 不要这么做！
```

#### 典型应用场景

```java
// 场景1：配置信息列表（读远多于写）
CopyOnWriteArrayList<Filter> filters = new CopyOnWriteArrayList<>();
// 启动时加载配置（写一次），运行时大量读取（无锁）
public List<Filter> getFilters() {
    return filters;  // 每次返回的都是一致的快照
}

// 场景2：白名单/黑名单（变更不频繁）
CopyOnWriteArrayList<String> whitelist = new CopyOnWriteArrayList<>();
whitelist.add("admin@company.com");

// ⚠️ 不适合的场景：高频写（如消息队列、消费记录）
//      每次写都复制整个数组，内存和 CPU 开销巨大
```

---

### 8.5.2 ConcurrentLinkedQueue

#### 无界非阻塞队列

基于**CAS + 链表**实现的无界线程安全队列。

```java
ConcurrentLinkedQueue<String> queue = new ConcurrentLinkedQueue<>();

queue.offer("A");  // 入队
queue.offer("B");
queue.poll();      // 出队，返回 "A"
queue.peek();      // 查看队首，不移除，返回 "B"

// 特点：
// - 无界（Integer.MAX_VALUE），offer 永不阻塞
// - 无锁读（volatile）
// - 写用 CAS 保证原子性
// - size() 需遍历，慎用
```

#### 与 LinkedBlockingQueue 对比

| 特性 | ConcurrentLinkedQueue | LinkedBlockingQueue |
|------|----------------------|---------------------|
| 队列长度 | 无界（MAX_VALUE） | 可有界可无界 |
| 阻塞操作 | 无（offer 不阻塞） | 有（put/take 会阻塞） |
| 吞吐量 | 更高 | 较低 |
| 适用场景 | 低延迟、无阻塞需求 | 需要背压（back-pressure）控制 |
| 迭代器 | weakly consistent | weakly consistent |

---

### 8.5.3 并发集合全景图

| 集合 | 底层结构 | 线程安全方式 | 特点 |
|------|---------|------------|------|
| `ConcurrentHashMap` | 数组+链表+红黑树 | CAS + synchronized | 高并发 Map 首选 |
| `ConcurrentLinkedQueue` | 无界链表 | CAS | 非阻塞，高吞吐量 |
| `ConcurrentLinkedDeque` | 无界双向链表 | CAS | 双端操作 |
| `CopyOnWriteArrayList` | 数组 | ReentrantLock | 读多写少场景 |
| `CopyOnWriteArraySet` | 包装 COWList | ReentrantLock | 同上 |
| `LinkedBlockingQueue` | 链表 | 两把锁 | 阻塞，业界首选 |
| `ArrayBlockingQueue` | 数组 | 一把锁 | 阻塞，有界 |
| `PriorityBlockingQueue` | 堆 | ReentrantLock | 优先级阻塞 |
| `DelayQueue` | 堆 + ReentrantLock | Delayed 接口 | 延迟队列 |
| `SynchronousQueue` | 无存储 | 两条栈/队列 | 直接传递 |
| `ConcurrentSkipListMap` | 跳表 | CAS | 并发+有序 Map |
| `ConcurrentSkipListSet` | 包装 CSLMap | CAS | 并发+有序 Set |

---

## 8.6 fail-fast 与 fail-safe 机制详解

### 8.6.1 概念定义

| 机制 | 全称 | 行为 | 抛出异常 | 典型实现 |
|------|------|------|---------|---------|
| **fail-fast** | Fast-Fail | 检测到并发修改，立即抛出异常 | `ConcurrentModificationException` | HashMap, ArrayList, HashSet |
| **fail-safe** | Fail-Safe | 检测到并发修改，**忽略**继续迭代（基于快照） | **不抛异常** | CopyOnWriteArrayList, ConcurrentHashMap, 迭代器快照 |

### 8.6.2 fail-fast 原理：modCount

```java
// AbstractList 中的 modCount 机制
protected transient int modCount = 0;  // 结构性修改次数

// 每当 add/remove/clear 等结构性操作，modCount++
public boolean add(E e) {
    modCount++;
    // ...
}

// 迭代器在创建时记录 expectedModCount = modCount
private class Itr implements Iterator<E> {
    int expectedModCount = modCount;

    public E next() {
        if (modCount != expectedModCount)
            throw new ConcurrentModificationException();  // 检测到修改，立即失败
        // ...
    }
}

// 示例：单线程下的"伪并发"也会触发 fail-fast
List<String> list = new ArrayList<>(Arrays.asList("A", "B", "C"));
for (String s : list) {        // for-each 底层用 Iterator
    if (s.equals("B")) {
        list.remove(s);        // ❌ 直接 remove 而非迭代器.remove()
    }                           //    导致 modCount++ != expectedModCount
}                               //    抛出 ConcurrentModificationException
```

### 8.6.3 fail-fast 的常见场景与规避

```java
// 场景1：for-each / iterator 遍历时修改集合
List<Integer> list = new ArrayList<>(Arrays.asList(1, 2, 3, 4, 5));

// ❌ 错误：for-each 中 remove
for (Integer i : list) {
    if (i % 2 == 0) list.remove(i);
}

// ✅ 正确1：使用 Iterator.remove()
Iterator<Integer> it = list.iterator();
while (it.hasNext()) {
    if (it.next() % 2 == 0) {
        it.remove();  // 迭代器内部同步了 modCount
    }
}

// ✅ 正确2：倒序遍历（避免索引错位）
for (int i = list.size() - 1; i >= 0; i--) {
    if (list.get(i) % 2 == 0) list.remove(i);
}

// ✅ 正确3：JDK8+ removeIf
list.removeIf(i -> i % 2 == 0);

// ✅ 正确4：使用 fail-safe 集合
CopyOnWriteArrayList<Integer> safeList = new CopyOnWriteArrayList<>(list);
for (Integer i : safeList) {  // 快照迭代，不抛异常
    list.remove(i);            // 操作原 list
}
// 输出 safeList 仍为 [1,2,3,4,5]
```

### 8.6.4 fail-safe 实现原理

```java
// CopyOnWriteArrayList 的迭代器
static final class COWIterator<E> implements ListIterator<E> {
    private final Object[] snapshot;  // 创建时的数组快照
    private int cursor;

    public COWIterator(Object[] elements, int initialCursor) {
        snapshot = elements;  // 直接引用当前数组（快照）
        cursor = initialCursor;
    }

    public E next() {
        return (E) snapshot[cursor++];  // 读快照，永不抛 CME
    }

    // ❌ 不支持 add/set/remove —— throw UnsupportedOperationException
    public void remove() {
        throw new UnsupportedOperationException();
    }
}

// ConcurrentHashMap 的迭代器（弱一致性）
// 遍历时其他线程的写入可能看到也可能看不到（不保证）
// 不会抛 ConcurrentModificationException
```

### 8.6.5 对比总结

| 维度 | fail-fast | fail-safe |
|------|----------|----------|
| 检测方式 | 计数器（modCount vs expectedModCount） | 快照或无检测 |
| 并发修改 | 立即抛出 CME | 忽略或弱一致 |
| 内存开销 | 低 | 高（快照复制） |
| 迭代器支持写 | 否（抛异常） | 否（通常不支持） |
| 代表集合 | HashMap, ArrayList, HashSet | CopyOnWriteArrayList, ConcurrentHashMap |
| 适用场景 | 非并发遍历 | 并发环境遍历 |

> 💡 **一句话总结**：  
> fail-fast 是**快速失败**策略，宁可抛异常也不给你错误数据；  
> fail-safe 是**安全继续**策略，读快照或忽略并发修改，保证不抛异常但不保证数据最新。

---

## 8.7 集合选型指南与性能对比

### 8.7.1 List 选型

| 场景 | 推荐 | 原因 |
|------|------|------|
| 99%场景 | `ArrayList` | 随机访问 O(1)，缓存友好，现代 JVM 性能优秀 |
| 频繁头插/中间删 | `LinkedList` | O(1) 插入/删除（但需先 O(n) 定位） |
| 线程安全（低并发） | `Collections.synchronizedList()` | 简单场景 |
| 高并发读多写少 | `CopyOnWriteArrayList` | 读无锁，写复制 |
| 高并发读写均衡 | `Vector`（不推荐）或 `ConcurrentLinkedQueue` | 视具体场景 |
| 模拟栈 | `ArrayDeque`（不要用 Stack） | 更高效率 |

### 8.7.2 Set 选型

| 场景 | 推荐 | 原因 |
|------|------|------|
| 通用去重 | `HashSet` | O(1) 插入/查找，最常用 |
| 保持插入顺序去重 | `LinkedHashSet` | 去重 + FIFO |
| 需要有序去重 | `TreeSet` | 红黑树，O(log n) |
| 高并发去重 | `ConcurrentHashMap.newKeySet()` | 高效并发 Set |

### 8.7.3 Map 选型

| 场景 | 推荐 | 原因 |
|------|------|------|
| 通用键值存储 | `HashMap` | O(1)，性能最优 |
| 需要插入顺序 | `LinkedHashMap` | 双向链表维护顺序 |
| 需要 key 排序 | `TreeMap` | 红黑树，自然序/自定义序 |
| 高并发安全 | `ConcurrentHashMap` | CAS + synchronized，高并发首选 |
| 高并发+有序 | `ConcurrentSkipListMap` | 跳表，有序 + 并发 |
| LRU 缓存 | `LinkedHashMap`(accessOrder=true) + 自定义 | 最简实现 |
| 弱引用缓存 | `WeakHashMap` | key 无引用时自动回收 |

### 8.7.4 Queue 选型

| 场景 | 推荐 | 原因 |
|------|------|------|
| 普通 FIFO | `ArrayDeque` | 比 LinkedList 快 |
| 线程安全 FIFO | `LinkedBlockingQueue` | 两把锁，高吞吐 |
| 有界队列 | `ArrayBlockingQueue` | 有界，公平可选 |
| 优先级调度 | `PriorityQueue`（单线程）/ `PriorityBlockingQueue` | 堆结构 |
| 定时延迟任务 | `DelayQueue` | 按延迟排序 |
| 线程间直接传递 | `SynchronousQueue` | 无存储，点对点 |
| 高性能无界 | `ConcurrentLinkedQueue` | CAS，非阻塞 |

### 8.7.5 性能对比速查

#### Map 性能（理论复杂度）

| 操作 | HashMap | LinkedHashMap | TreeMap | ConcurrentHashMap |
|------|---------|--------------|---------|-------------------|
| get | O(1) 均摊 | O(1) | O(log n) | O(1) 均摊 |
| put | O(1) 均摊 | O(1) 均摊 | O(log n) | O(1) 均摊 |
| containsKey | O(1) 均摊 | O(1) | O(log n) | O(1) 均摊 |
| 有序遍历 | ❌ | ✅ | ✅ | ❌（但 ConcurrentSkipListMap 可） |
| 线程安全 | ❌ | ❌ | ❌ | ✅ |
| 迭代安全性 | fail-fast | fail-fast | fail-fast | fail-safe |

#### List 性能

| 操作 | ArrayList | LinkedList | Vector |
|------|----------|-----------|--------|
| get(i) | **O(1)** | O(n) | O(1) |
| add(E)（尾部） | O(1) 均摊 | O(1) | O(1) 均摊 |
| add(i, E)（中间） | O(n) | O(1)（先 O(n) 找位置） | O(n) |
| remove(i) | O(n) | O(1)（先 O(n) 找位置） | O(n) |
| 迭代器 remove | O(1) | O(1) | O(1) |
| 内存局部性 | 好（连续） | 差（节点分散） | 好（连续） |
| 线程安全 | ❌ | ❌ | ✅（全局锁） |

---

### 8.7.6 最佳实践与常见坑

#### 坑 1：HashMap 容量规划

```java
// ❌ 低估初始容量，导致频繁扩容（扩容成本很高）
Map<Integer, String> bad = new HashMap<>();  // 默认16，负载0.75，扩容阈值12

// ✅ 预估容量，减少扩容次数
// 预计 1000 个元素：1000 / 0.75 ≈ 1333，取 2 的幂 → 2048
Map<Integer, String> good = new HashMap<>(2048);
```

#### 坑 2：对象作为 HashMap key 时忘记覆写 hashCode/equals

```java
// ❌ 两个逻辑相等的 Student 对象，因为没有覆写 hashCode/equals
//    导致 HashMap 认为它们是不同的 key
class Student {
    private String name;
    private int age;
    // ❌ 忘记覆写 hashCode 和 equals
}

Student s1 = new Student("张三", 18);
Student s2 = new Student("张三", 18);

Map<Student, Integer> map = new HashMap<>();
map.put(s1, 90);
map.get(s2);  // ❌ null —— s1 和 s2 的 hashCode 不同，无法匹配！

// ✅ 正确覆写
@Override
public int hashCode() {
    return Objects.hash(name, age);
}
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    Student that = (Student) o;
    return age == that.age && Objects.equals(name, that.name);
}
```

#### 坑 3：ConcurrentHashMap 的空值

```java
// ❌ ConcurrentHashMap 不允许 null key/value
ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();
map.put("A", null);   // NullPointerException！
map.put(null, 1);    // NullPointerException！

// ✅ 正确：用 Optional 或 -1 表示不存在
map.put("A", 0);       // 0 可能和"不存在"混淆
map.containsKey("A"); // 先检查再取值
```

#### 坑 4：用 LinkedList 当队列（效率低下）

```java
// ❌ 用 LinkedList 当 Queue —— 内存碎片化，指针开销大
Queue<String> q = new LinkedList<>();

// ✅ 用 ArrayDeque —— 数组实现，缓存友好，性能高 3 倍
Queue<String> q2 = new ArrayDeque<>();
```

#### 坑 5：HashMap vs ConcurrentHashMap 在单线程下的选择

```java
// ❌ 过度设计：单线程用 ConcurrentHashMap（不必要地牺牲性能）
ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();
map.put("A", 1);  // CAS 开销

// ✅ 单线程场景用 HashMap
Map<String, Integer> map = new HashMap<>();
map.put("A", 1);
```

---

## 8.8 常见面试题

### Q1：HashMap 的容量为什么必须是 2 的幂？

HashMap 通过 `(n - 1) & hash` 来计算桶下标。当 `n = 2^k` 时，`n - 1` 的二进制是 `k` 个 `1`，`& hash` 操作等价于 `hash % n`，但位运算比取模快得多。如果 `n` 不是 2 的幂，`&` 就无法均匀散列，会产生大量哈希冲突。

---

### Q2：HashMap 为什么选择 0.75 作为负载因子？

- **太低**（如 0.5）：扩容频繁，空间浪费严重
- **太高**（如 1.0）：哈希冲突加剧，链表/红黑树变长，查找变慢
- **0.75** 是时间-空间成本的最佳平衡点：扩容不频繁，同时链表较短，查找性能可控

---

### Q3：HashMap 和 Hashtable 的区别？

| | HashMap | Hashtable |
|--|---------|-----------|
| 线程安全 | ❌ | ✅（全局锁） |
| null key/value | 各允许一个 | 都不允许 |
| 初始容量 | 16 | 11 |
| 扩容策略 | 2n | 2n+1 |
| 迭代器 | fail-fast | fail-fast（枚举器） |
| 推荐 | ✅ | ❌（已废弃） |

---

### Q4：ConcurrentHashMap 和 Hashtable 的区别？

| | ConcurrentHashMap | Hashtable |
|--|-------------------|-----------|
| 锁粒度 | 桶级别（细） | 表级别（粗） |
| 并发度 | 高（可多线程并发写） | 低（全表锁） |
| 读操作 | 无锁（volatile） | 有锁（synchronized） |
| null key/value | 都不允许 | 都不允许 |
| 吞吐量 | 高 | 低 |
| JDK 版本 | 1.5+ | 1.0（早于集合框架） |

---

### Q5：ConcurrentHashMap 在 JDK7 和 JDK8 有什么区别？

| | JDK7 | JDK8 |
|--|------|------|
| 锁机制 | Segment 分段锁（ReentrantLock） | CAS + synchronized |
| 数据结构 | Segment[] + HashMap | Node[] + 链表 + 红黑树 |
| 锁粒度 | Segment（多个桶） | 单个桶 |
| 扩容 | 单线程扩容 | 多线程并发扩容 |
| 并发度上限 | Segment 数量（默认16） | 桶数量（可动态增长） |

---

### Q6：HashMap 的死链问题（重点！）

JDK7 中，扩容时使用**头插法**，会导致链表反转。两个线程同时扩容时，链表可能形成环形结构，导致 `get()` 死循环（CPU 100%）。

```java
// JDK7 transfer() 中的问题代码
void transfer(Entry[] newTable) {
    Entry[] src = table;
    int newCapacity = newTable.length;
    for (int j = 0; j < src.length; j++) {
        Entry<K,V> e = src[j];
        if (e != null) {
            src[j] = null;  // 释放旧表
            do {
                Entry<K,V> next = e.next;   // 记录下一个
                e.next = newTable[i];       // 头插法！反转链表
                newTable[i] = e;
                e = next;
            } while (e != null);
        }
    }
}
```

JDK8 改为**尾插法**，且引入红黑树，彻底避免死链问题。

> ⚠️ 但 HashMap 本身**永远不要**在并发环境中使用，即使 JDK8 也无法保证并发安全。

---

### Q7：ConcurrentHashMap 的 get 是否需要加锁？

**不需要**。get 操作直接读 `table`（volatile 数组），通过 `Unsafe.getObjectVolatile` 保证可见性。put 时如果发现目标桶正在被另一个线程迁移（`f.hash == MOVED`），会先协助扩容再继续。

---

### Q8：fail-fast 和 fail-safe 的区别？

- **fail-fast**：迭代器创建时记录 `expectedModCount`，后续 `modCount` 变化则抛 `ConcurrentModificationException`。代表：`HashMap`、`ArrayList`
- **fail-safe**：基于快照或无检测，并发修改不抛异常。代表：`CopyOnWriteArrayList`、`ConcurrentHashMap` 迭代器

---

### Q9：CopyOnWriteArrayList 适合什么场景？

**读多写少**的低并发场景：
- 配置/规则列表（启动加载，运行期几乎不变）
- 白名单/黑名单（变更频率极低）
- **不适合**：高频写场景（每次写都复制整个数组，内存和 CPU 开销巨大）

---

### Q10：ArrayList 和 LinkedList 如何选择？

| 判断维度 | 结论 |
|---------|------|
| 大部分增删改查 | `ArrayList`（连续内存，JVM 缓存友好） |
| 需要在头部/中间频繁插入 | `LinkedList`（但先 O(n) 定位） |
| 需要实现 Queue/Deque | `ArrayDeque`（比 LinkedList 快） |
| 大数据量（百万级随机插入） | 测试后决定（JVM 现代优化让 ArrayList 差距缩小） |

---

### Q11：Queue 和 Deque 的区别？

- **Queue**：单端队列，只能从队尾入队、队首出队（FIFO）
- **Deque**：双端队列，可以从任意一端入队/出队
- Deque 兼容 Queue，同时可以当**栈**使用（`push()`/`pop()`）

---

### Q12：阻塞队列和非阻塞队列的区别？

| | 阻塞队列 | 非阻塞队列 |
|--|---------|-----------|
| 操作 | 队满/队空时会**阻塞等待** | 立即返回（offer/poll） |
| 实现 | `ReentrantLock` + `Condition` | `CAS` |
| 典型 | `LinkedBlockingQueue`, `ArrayBlockingQueue` | `ConcurrentLinkedQueue`, `ArrayDeque` |
| 适用 | 生产者-消费者模式，需要背压控制 | 高性能需求，无需阻塞等待 |

---

## 📌 本章小结

Ch08 在 Ch04 基础上，深入了 Java 集合框架的**进阶知识**：

### 核心知识点

| 模块 | 重点 |
|------|------|
| **HashMap 原理** | 寻址机制、扩容流程、JDK8 红黑树、线程不安全原因 |
| **TreeMap** | 红黑树实现、有序操作（subMap/lower/higher） |
| **LinkedHashMap** | 双向链表机制、LRU 缓存实现 |
| **Hashtable** | 历史包袱、全局锁、与 HashMap 的核心区别 |
| **Queue/Deque** | 阻塞 vs 非阻塞、ArrayDeque vs LinkedList、BlockingQueue 家族 |
| **ConcurrentHashMap** | JDK7 分段锁 → JDK8 CAS+Synchronized、扩容机制、桶锁 |
| **CopyOnWriteArrayList** | 读写分离、写时复制、读多写少场景 |
| **fail-fast vs fail-safe** | modCount 机制、快照迭代、弱一致性 |
| **集合选型** | 按场景选择合适的集合，避免过度设计 |

### 面试高频词

```
HashMap 死链 / JDK8 红黑树 / ConcurrentHashMap CAS / 分段锁
负载因子 0.75 / 容量 2 的幂 / 扩容机制 / modCount
```

---

**下一章：Ch09 - 并发编程**，我们将深入 Java 并发的核心机制，包括线程基础、`synchronized`、`volatile`、`JUC` 工具包、锁原理、死锁与活锁等高频面试内容。
