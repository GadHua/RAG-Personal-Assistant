# Ch04 - 集合框架

## 4.1 集合概述

### 为什么需要集合

数组长度固定，无法动态扩容。集合可以存储任意数量的对象，提供增删改查等丰富操作。

### 集合体系结构

```
Collection（单列）
├── List（有序、可重复）
│   ├── ArrayList（数组实现）
│   ├── LinkedList（双向链表实现）
│   └── Vector（数组实现，线程安全）
│       └── Stack
└── Set（无序、去重）
    ├── HashSet（哈希表）
    │   └── LinkedHashSet（保持插入顺序）
    └── TreeSet（红黑树，有序）

Map（双列，键值对）
├── HashMap（哈希表）
│   └── LinkedHashMap（保持插入顺序）
├── TreeMap（红黑树，按 key 排序）
├── Hashtable（哈希表，线程安全）
└── ConcurrentHashMap（分段锁）
```

### 集合与数组的区别

| 区别 | 数组 | 集合 |
|------|------|------|
| 长度 | 固定 | 动态 |
| 类型 | 基本类型 + 引用 | 仅引用类型 |
| 功能 | 单一 | 丰富（增删改查排序等） |
| 内存 | 连续 | 不一定连续 |

---

## 4.2 List 接口

### 特点

- **有序**：元素按插入顺序存储
- **可重复**：允许存储相同元素
- **有索引**：可通过下标访问元素

### 主要实现类

| 类 | 底层结构 | 线程安全 | 适用场景 |
|---|---------|---------|---------|
| ArrayList | 数组 | 否 | 随机访问，尾插 |
| LinkedList | 双向链表 | 否 | 频繁插入删除 |
| Vector | 数组 | 是 | 需线程安全时 |

---

## 4.3 ArrayList

### 核心特性

- 底层是**动态数组**
- 默认初始容量 **10**
- 扩容系数 **1.5 倍**（`oldCapacity + (oldCapacity >> 1)`）
- 线程不安全，性能高

### 基本操作

```java
List<String> list = new ArrayList<>();

//添加
list.add("A");
list.add("B");
list.add(1, "C");  //指定位置插入

//删除
list.remove(0);        //删除索引0
list.remove("A");      //删除元素"A"

//修改
list.set(0, "X");      //修改索引0

//查询
list.get(0);           //获取索引0
list.size();           //长度
list.contains("A");   //是否包含
list.indexOf("B");     //查找索引，不存在返回-1
list.isEmpty();        //是否为空

//遍历
for (int i = 0; i < list.size(); i++) {
    System.out.println(list.get(i));
}

for (String s : list) {
    System.out.println(s);
}

//迭代器
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    String s = it.next();
    System.out.println(s);
}

//ListIterator（可向前向后，可修改）
ListIterator<String> lit = list.listIterator();
while (lit.hasNext()) {
    lit.next();
}
while (lit.hasPrevious()) {
    System.out.println(lit.previous());
}
```

### 底层原理

```java
//ArrayList 内部结构
transient Object[] elementData;  //存储元素的数组
private int size;                //实际元素个数

//add 方法核心逻辑
public boolean add(E e) {
    ensureCapacityInternal(size + 1);  //确保容量够用
    elementData[size++] = e;            //插入元素
    return true;
}

//扩容逻辑
private void grow(int minCapacity) {
    int oldCapacity = elementData.length;
    int newCapacity = oldCapacity + (oldCapacity >> 1);  //1.5倍
    if (newCapacity - minCapacity < 0)
        newCapacity = minCapacity;
    elementData = Arrays.copyOf(elementData, newCapacity);
}
```

### 初始化方式对比

```java
//方式1：默认构造，空数组，第一次 add 才分配容量
List<String> list1 = new ArrayList<>();

//方式2：指定初始容量（减少扩容次数）
List<String> list2 = new ArrayList<>(100);

//方式3：从已有集合创建
List<String> list3 = new ArrayList<>(Arrays.asList("A", "B", "C"));
```

### 转换为数组

```java
List<String> list = new ArrayList<>(Arrays.asList("A", "B", "C"));

String[] arr1 = list.toArray(new String[0]);  //推荐，效率更高
String[] arr2 = list.toArray(new String[list.size()]);
```

---

## 4.4 LinkedList

### 核心特性

- 底层是**双向链表**
- 线程不安全
- 插入/删除效率高（O(1)），查询效率低（O(n)）

### 节点结构

```java
private static class Node<E> {
    E item;
    Node<E> prev;
    Node<E> next;
    Node(Node<E> prev, E element, Node<E> next) {
        this.item = element;
        this.prev = prev;
        this.next = next;
    }
}
```

### 基本操作

```java
LinkedList<String> list = new LinkedList<>();

//特有操作
list.addFirst("A");     //头部插入
list.addLast("B");      //尾部插入
list.removeFirst();     //头部删除
list.removeLast();      //尾部删除
list.getFirst();        //获取头
list.getLast();         //获取尾
list.peek();            //获取头，不删除
list.poll();            //获取并删除头
list.push("X");         //压栈（相当于 addFirst）
list.pop();            //弹栈（相当于 removeFirst）

//通用操作（继承自 List）
list.add("C");
list.get(0);
list.size();
```

### ArrayList vs LinkedList

| 操作 | ArrayList | LinkedList |
|------|----------|------------|
| 随机访问 get(i) | O(1) | O(n) |
| 头部插入 | O(n) | O(1) |
| 尾部插入 | O(1) 均摊 | O(1) |
| 中间插入 | O(n) | O(1) 但需先遍历 |
| 内存占用 | 连续，节省指针 | 节点+指针，额外开销 |

**选择建议：**
- 大部分场景用 **ArrayList**（现代 JVM 数组连续访问很快）
- 频繁在头部/中间插入删除，用 **LinkedList**
- 想要 FIFO 队列，用 **ArrayDeque**（比 LinkedList 更高效）

---

## 4.5 Vector 与 Stack

### Vector

- 底层是**数组**
- **线程安全**（ synchronized 修饰方法）
- 扩容**2倍**
- 被 ArrayList 替代，慎用

```java
Vector<String> v = new Vector<>();
v.add("A");
v.get(0);
```

### Stack

- 继承 Vector，**后进先出（LIFO）**
- `push()` 压栈
- `pop()` 弹栈
- `peek()` 查看栈顶

```java
Stack<Integer> stack = new Stack<>();
stack.push(1);
stack.push(2);
stack.push(3);

stack.pop();  //3
stack.pop();  //2
stack.peek(); //1
```

**注意：Stack 已过时**，推荐使用 `ArrayDeque`

```java
Deque<Integer> stack = new ArrayDeque<>();
stack.push(1);
stack.pop();
```

---

## 4.6 Set 接口

### 特点

- **无序**：不保证迭代顺序
- **去重**：相同元素只存一个（equals 和 hashCode 决定）

### 主要实现类

| 类 | 底层结构 | 排序 | 线程安全 |
|---|---------|------|---------|
| HashSet | 哈希表 | 无序 | 否 |
| LinkedHashSet | 哈希表 + 链表 | 插入顺序 | 否 |
| TreeSet | 红黑树 | 自然顺序/自定义 | 否 |

---

## 4.7 HashSet

### 核心特性

- 底层基于 **HashMap**（所有元素存在 HashMap 的 key）
- **无序**
- **线程不安全**
- 允许存 `null`（只能一个）
- 添加元素时自动去重

### 基本操作

```java
Set<String> set = new HashSet<>();

set.add("A");
set.add("B");
set.add("A");  //重复，添加失败

set.size();       //2
set.contains("A");//true
set.remove("A");
set.isEmpty();

for (String s : set) {
    System.out.println(s);
}

Iterator<String> it = set.iterator();
while (it.hasNext()) {
    System.out.println(it.next());
}
```

### 去重原理

HashSet 判断两个元素相同，需要满足：

1. `hashCode()` 相等
2. `equals()` 返回 `true`

```java
public class Student {
    private String name;
    private int age;
    
    @Override
    public int hashCode() {
        return Objects.hash(name, age);
    }
    
    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;
        Student other = (Student) obj;
        return Objects.equals(name, other.name) && age == other.age;
    }
}
```

### 负载因子

```java
//HashSet 内部
static final float DEFAULT_LOAD_FACTOR = 0.75f;

//当元素数量 > 容量 * 负载因子 时，扩容 2 倍
//默认容量 16，存第 13 个元素时触发扩容
```

---

## 4.8 LinkedHashSet

- 继承 HashSet
- 底层是 **LinkedHashMap**
- 保持**插入顺序**
- 其他特性同 HashSet

```java
Set<String> set = new LinkedHashSet<>();
set.add("C");
set.add("A");
set.add("B");
//迭代顺序：C -> A -> B（插入顺序）
```

---

## 4.9 TreeSet

### 核心特性

- 底层基于 **TreeMap**（红黑树）
- **有序**：按自然顺序或自定义比较器排序
- **线程不安全**
- **不能存 null**（需要比较）
- 元素必须实现 `Comparable` 或构造时传入 `Comparator`

### 基本操作

```java
Set<Integer> set = new TreeSet<>();

set.add(3);
set.add(1);
set.add(2);
//迭代顺序：1 -> 2 -> 3（自然升序）

set.first();  //最小
set.last();   //最大
set.lower(2); //小于2的最大
set.higher(2);//大于2的最小
set.headSet(3);    //小于3的子集
set.tailSet(2);    //大于等于2的子集
set.subSet(1, 3);  //[1, 3) 子集
```

### 自定义排序

```java
//方式1：元素实现 Comparable
class Person implements Comparable<Person> {
    private String name;
    private int age;
    
    @Override
    public int compareTo(Person o) {
        //按年龄升序
        return this.age - o.age;
    }
}

//方式2：构造时传入 Comparator
Set<Person> set = new TreeSet<>(new Comparator<Person>() {
    @Override
    public int compare(Person p1, Person p2) {
        //按年龄升序
        return p1.getAge() - p2.getAge();
    }
});

//JDK 8+ lambda
Set<Person> set = new TreeSet<>((p1, p2) -> p1.getAge() - p2.getAge());
```

---

## 4.10 Map 接口

### 特点

- **键值对**：key-value 形式存储
- **key 唯一**：HashMap 的 key 去重（equals + hashCode）
- **value 可重复**
- 一个 key 对应一个 value

### 主要实现类

| 类 | 底层结构 | 排序 | 线程安全 |
|---|---------|------|---------|
| HashMap | 哈希表 | 无序 | 否 |
| LinkedHashMap | 哈希表 + 链表 | 插入顺序 | 否 |
| TreeMap | 红黑树 | key 排序 | 否 |
| Hashtable | 哈希表 | 无序 | 是（过时） |
| ConcurrentHashMap | 分段锁 | 无序 | 是 |

---

## 4.11 HashMap

### 核心特性

- **线程不安全**
- key 允许 null（只能一个）
- value 允许 null（多个）
- 无序

### 基本操作

```java
Map<String, Integer> map = new HashMap<>();

//添加/修改
map.put("Java", 98);
map.put("Python", 87);
map.put("C++", 92);
map.put("Java", 100);  //key 相同，value 覆盖

//删除
map.remove("Python");
map.clear();  //清空

//查询
map.get("Java");           //98，不存在返回 null
map.getOrDefault("Go", 0); //不存在返回默认值 0
map.containsKey("Java");   //true
map.containsValue(100);   //true
map.size();                //3
map.isEmpty();

//遍历方式1：遍历 key
for (String key : map.keySet()) {
    System.out.println(key + "=" + map.get(key));
}

//遍历方式2：遍历 entry
for (Map.Entry<String, Integer> entry : map.entrySet()) {
    System.out.println(entry.getKey() + "=" + entry.getValue());
}

//遍历方式3：遍历 value
for (Integer value : map.values()) {
    System.out.println(value);
}
```

### 底层原理：数组 + 链表 + 红黑树

JDK 1.8+ 实现：

```java
//HashMap 内部结构
transient Node<K,V>[] table;  //哈希表（数组）

//Node（链表节点）
static class Node<K,V> {
    final int hash;
    final K key;
    V value;
    Node<K,V> next;  //指向下一个节点
}

//当链表长度 > 8 且数组长度 >= 64 时，链表转为红黑树
//红黑树节点
static final class TreeNode<K,V> extends LinkedHashMap.Entry<K,V> {
    TreeNode<K,V> parent;
    TreeNode<K,V> left;
    TreeNode<K,V> right;
    boolean red;  //红黑树的颜色
}
```

### put 流程

```
put("name", "Tom")
     ↓
1. 计算 key 的 hash 值（扰动函数处理，减少碰撞）
2. 计算数组下标位置
3. 如果该位置为空，直接插入
4. 如果该位置有元素（链表）：
   - 遍历链表，比较 hash 和 equals
   - key 已存在，覆盖 value
   - key 不存在，插入链表尾部
   - 链表长度 > 8，转换为红黑树
5. 如果该位置是红黑树，插入树中
6. 检查是否需要扩容
```

### hash 计算（扰动函数）

```java
//JDK 7：直接 hashCode
int hash = key.hashCode();
int h = hash ^ (hash >>> 16);

//JDK 8+：二次哈希优化
static final int hash(Object key) {
    int h;
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}

//下标计算：n 是数组长度（2的幂次）
int index = (n - 1) & hash;
```

### 扩容机制

```java
//默认容量 16，负载因子 0.75
//当 size > capacity * 0.75 时扩容

//扩容逻辑
void resize() {
    Node<K,V>[] oldTab = table;
    int oldCap = (oldTab == null) ? 0 : oldTab.length;
    int oldThr = threshold;  //oldCap * loadFactor
    
    int newCap, newThr = 0;
    newCap = oldCap << 1;  //容量翻倍
    newThr = oldThr << 1; //阈值翻倍
    
    threshold = newThr;    //下次扩容阈值
    table = newTab;
    
    //迁移数据（重新计算所有元素位置）
}
```

### 初始化方式

```java
//方式1：默认（容量16，负载因子0.75）
Map<String, Integer> map1 = new HashMap<>();

//方式2：指定容量（实际容量会是最近的2的幂）
Map<String, Integer> map2 = new HashMap<>(100);

//方式3：指定容量和负载因子
Map<String, Integer> map3 = new HashMap<>(100, 0.5f);

//方式4：从已有 Map 创建
Map<String, Integer> map4 = new HashMap<>(map1);
```

---

## 4.12 LinkedHashMap

- 继承 HashMap
- 内部维护**双向链表**保持插入顺序
- 适合需要记录访问顺序的场景（如 LRU 缓存）

```java
Map<String, Integer> map = new LinkedHashMap<>();
map.put("A", 1);
map.put("C", 3);
map.put("B", 2);
//迭代顺序：A -> C -> B（插入顺序）
```

---

## 4.13 TreeMap

### 特点

- 基于**红黑树**
- 按 **key 排序**（自然顺序或自定义 Comparator）
- **key 不能为 null**
- 线程不安全

### 基本操作

```java
Map<String, Integer> map = new TreeMap<>();

map.put("banana", 2);
map.put("apple", 1);
map.put("cherry", 3);
//key 按字母排序：apple -> banana -> cherry

map.firstKey();       //最小 key
map.lastKey();        //最大 key
map.lowerKey("cherry"); //小于 cherry 的最大
map.higherKey("apple"); //大于 apple 的最小
map.subMap("apple", "cherry"); //[apple, cherry) 子map
```

---

## 4.14 Hashtable vs ConcurrentHashMap

### Hashtable（过时）

- 线程安全（synchronized 修饰每个方法）
- 性能差，不推荐使用
- key/value 都不能为 null

```java
Hashtable<String, Integer> table = new Hashtable<>();
table.put("A", 1);  //线程安全，但效率低
```

### ConcurrentHashMap（推荐）

- 线程安全
- JDK 7：分段锁（Segment）
- JDK 8+：`CAS + synchronized`，锁住单个桶
- 性能高，并发场景首选
- key/value 都不能为 null

```java
ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();
map.put("A", 1);
map.get("A");
```

---

## 4.15 Collections 工具类

### 常用方法

```java
List<Integer> list = new ArrayList<>(Arrays.asList(3, 1, 4, 1, 5));

//排序
Collections.sort(list);              //自然升序
Collections.reverse(list);          //反转
Collections.shuffle(list);           //随机打乱

//查找
int index = Collections.binarySearch(list, 4);  //二分查找，必须先排序
Collections.max(list);               //最大
Collections.min(list);               //最小

//填充
Collections.fill(list, 0);           //所有元素设为0

//计数
int freq = Collections.frequency(list, 1);  //元素1出现次数

//交换
Collections.swap(list, 0, 2);        //交换索引0和2的元素

//添加
Collections.addAll(list, 7, 8, 9);   //批量添加

//不可变集合
List<Integer> unmodifiable = Collections.unmodifiableList(list);
Map<String, Integer> immutableMap = Collections.unmodifiableMap(map);

//线程安全集合
List<Integer> syncList = Collections.synchronizedList(new ArrayList<>());
Map<String, Integer> syncMap = Collections.synchronizedMap(new HashMap<>());
```

---

## 4.16 集合选择指南

| 场景 | 推荐 |
|------|------|
| 需要有序、去重 | TreeSet |
| 需要插入顺序、去重 | LinkedHashSet |
| 常用增删改查 | ArrayList |
| 频繁头插/删除 | LinkedList / ArrayDeque |
| 键值对存储 | HashMap |
| 需要 key 排序 | TreeMap |
| 需要插入顺序 | LinkedHashMap |
| 高并发场景 | ConcurrentHashMap |
| 需要栈结构 | ArrayDeque（不推荐 Stack） |

---

## 📌 本章小结

Ch04 覆盖了 Java 集合框架核心知识点：

- **List**：ArrayList（数组）、LinkedList（链表）、Vector（线程安全）
- **Set**：HashSet（去重无序）、LinkedHashSet（去重有序）、TreeSet（排序去重）
- **Map**：HashMap、LinkedHashMap、TreeMap、Hashtable、ConcurrentHashMap
- **底层原理**：哈希表、链表、红黑树、扩容机制、负载因子
- **工具类**：Collections

下一章：**Ch05 - 泛型与类型系统**，编译期类型安全机制。
