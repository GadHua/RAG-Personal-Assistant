# Ch12 - Java 新特性

## 摘要

> 本章系统讲解 Java 8 至 Java 21 的核心新特性，从最基础的 Lambda 表达式与函数式接口出发，深度解析 Stream API 的创建、中间操作与终止操作；深入并行流与 ForkJoinPool 的性能优化策略；全面覆盖 Optional 的链式调用与最佳实践；详解新 DateTime API 的 LocalDateTime、ZonedDateTime 与格式化；最后梳理 Java 14-21 的重要新语法——Record、Sealed Classes、Switch 表达式、Pattern Matching for instanceof 以及 Java 21 的虚拟线程（协程）。全文配以贴近实战的代码示例，剖析常见坑点，帮助读者建立从"会用"到"用好"的知识体系。

---

## 12.1 Lambda 表达式

### 12.1.1 Lambda 基础语法

**Lambda 表达式**是 Java 8 引入的函数式编程特性，本质是一段可以传递的代码块（匿名函数）。它允许将行为作为参数传递，让代码更简洁、表达力更强。

**语法结构：**

```java
(parameters) -> expression
// 或
(parameters) -> { statements; }
```

| 语法形式 | 规则 | 示例 |
|---------|------|------|
| 省略参数类型 | 编译器可推断时可不写 | `(a, b) -> a + b` |
| 单参数无括号 | 仅当类型推断明确时可用 | `list.forEach(s -> System.out.println(s))` |
| 单语句表达式 | 直接返回，无需 `return` | `(a, b) -> a + b` |
| 多语句块 | 需要 `return` 显式返回值 | `(a, b) -> { int sum = a + b; return sum; }` |
| 无参数 | 用空括号表示 | `() -> System.out.println("Hello")` |

**Java 类型系统对 Lambda 的约束：**

- **只能出现在需要函数式接口的地方**（Functional Interface）
- **参数类型由目标类型（Target Type）推断**
- **返回类型由表达式/语句推断，兼容目标类型**

```java
// Lambda 示例：最简形式
Runnable r = () -> System.out.println("Hello Lambda");
// 等价于
Runnable r2 = new Runnable() {
    @Override
    public void run() {
        System.out.println("Hello Anonymous");
    }
};
```

**常见坑：Lambda 表达式外部变量的作用域**

```java
// ❌ 常见错误：闭包中对外部变量修改（Effectively Final 限制）
int count = 0;
list.forEach(s -> {
    count++;  // 编译错误！Lambda 内无法修改外部非 final 变量
    System.out.println(s);
});

// ✅ 正确做法：用 AtomicInteger 或其他线程安全容器
AtomicInteger count = new AtomicInteger(0);
list.forEach(s -> {
    count.incrementAndGet();
    System.out.println(s);
});
```

> **Effective Final**：在 Lambda 表达式中使用外部变量时，该变量必须是 effectively final（即最终只赋值一次），否则编译报错。这是 Java 避免数据竞争的安全设计。

### 12.1.2 函数式接口（Functional Interface）

**函数式接口**是只包含一个抽象方法（Single Abstract Method, SAM）的接口。Java 8 专门新增了 `@FunctionalInterface` 注解，编译器会检查接口是否确实只有一个抽象方法。

```java
@FunctionalInterface
public interface MyFunction<T, R> {
    R apply(T t);  // 唯一的抽象方法

    // 可以有 default 方法（不影响 SAM 性质）
    default void log(String msg) {
        System.out.println("[LOG] " + msg);
    }
}
```

**Java 标准库中常用的函数式接口（java.util.function 包）：**

| 接口 | 方法签名 | 说明 | 示例 |
|------|---------|------|------|
| `Predicate<T>` | `boolean test(T t)` | 判断型 | `list.stream().filter(Predicate)` |
| `Consumer<T>` | `void accept(T t)` | 消费型 | `list.forEach(Consumer)` |
| `Supplier<T>` | `T get()` | 供给型 | `() -> new Object()` |
| `Function<T,R>` | `R apply(T t)` | 函数型 | `stream.map(Function)` |
| `UnaryOperator<T>` | `T apply(T t)` | 一元运算 | `list.replaceAll(UnaryOp)` |
| `BinaryOperator<T>` | `T apply(T t1, T t2)` | 二元运算 | `stream.reduce(BinaryOp)` |
| `BiFunction<T,U,R>` | `R apply(T t, U u)` | 双输入函数 | — |
| `BiConsumer<T,U>` | `void accept(T t, U u)` | 双输入消费 | `map.forEach(BiConsumer)` |

**函数式接口之间的转换（类型层次）：**

```
Function<T, R>
    ↓（参数的逆变 + 返回的协变）
BiFunction<T, U, R>

Predicate<T>
    ↑（Boolean 是 R 的子类型）
Function<T, Boolean>

Consumer<T>
    ↑（void 是返回类型的子类型）
Function<T, Void>
```

### 12.1.3 方法引用（Method Reference）

**方法引用**是 Lambda 表达式的一种简写形式，当 Lambda 体仅调用一个已有方法时，可以用 `::` 运算符直接引用。

**四种形式：**

| 类型 | 语法 | 等价 Lambda | 示例 |
|------|------|-----------|------|
| 静态方法引用 | `类名::静态方法名` | `(args) -> 类名.静态方法(args)` | `String::valueOf` |
| 实例方法引用（特定对象） | `对象::实例方法名` | `(args) -> obj.实例方法(args)` | `System.out::println` |
| 实例方法引用（任意对象） | `类名::实例方法名` | `(obj, args) -> obj.实例方法(args)` | `String::toUpperCase` |
| 构造方法引用 | `类名::new` | `() -> new 类名()` | `ArrayList::new` |

```java
public class MethodReferenceDemo {
    public static void main(String[] args) {
        List<String> names = Arrays.asList("alice", "bob", "charlie");

        // 1. 静态方法引用
        List<Integer> lengths = names.stream()
            .map(String::length)  // 等价于 s -> s.length()
            .collect(Collectors.toList());
        System.out.println(lengths);  // [5, 3, 7]

        // 2. 实例方法引用（特定对象）
        PrintStream out = System.out;
        names.forEach(out::println);
        // 等价于 names.forEach(s -> System.out.println(s));

        // 3. 实例方法引用（任意对象）
        List<String> upper = names.stream()
            .map(String::toUpperCase)  // 等价于 s -> s.toUpperCase()
            .collect(Collectors.toList());
        System.out.println(upper);  // [ALICE, BOB, CHARLIE]

        // 4. 构造方法引用
        List<ArrayList<String>> lists = names.stream()
            .map(ArrayList::new)  // 等价于 s -> new ArrayList<>(s)
            .collect(Collectors.toList());

        // 进阶：带参数的构造方法引用
        List<String> source = Arrays.asList("a", "b", "c");
        List<ArrayList<String>> initialized = source.stream()
            .map(arr -> new ArrayList<>(arr))  // 需包装一层
            .collect(Collectors.toList());
        // 更好写法：使用 Stream.of + toCollection
        List<ArrayList<String>> better = Stream.of("a", "b", "c")
            .map(ArrayList::new)
            .collect(Collectors.toCollection(ArrayList::new));
    }
}
```

**常见坑：方法引用 vs Lambda 的抉择**

```java
// ❌ 过度使用实例方法引用导致可读性差
list.stream()
    .map(String::toUpperCase)
    .filter(String::isEmpty)
    .collect(Collectors.toList());

// ✅ 当逻辑复杂时，用 Lambda 明确表达
list.stream()
    .map(s -> {
        String result = s.trim().toUpperCase();
        return result;
    })
    .filter(s -> s.length() > 5)
    .collect(Collectors.toList());

// 原则：逻辑简单用方法引用，逻辑复杂用 Lambda
```

### 12.1.4 组合与高级用法

**函数式接口的默认方法（组合能力）：**

```java
// Predicate 组合
Predicate<String> isNotEmpty = s -> !s.isEmpty();
Predicate<String> isLongEnough = s -> s.length() >= 5;
Predicate<String> startsWithA = s -> s.startsWith("A");

// and / or / negate
Predicate<String> combined = isNotEmpty.and(isLongEnough).and(startsWithA.negate());

List<String> result = names.stream()
    .filter(combined)
    .collect(Collectors.toList());

// Function 组合
Function<String, Integer> length = String::length;
Function<Integer, String> label = i -> "长度: " + i;
Function<String, String> pipeline = length.andThen(label);

String label = pipeline.apply("hello");  // "长度: 5"
```

---

## 12.2 Stream API

### 12.2.1 Stream 的创建

Stream 是 Java 8 引入的**延迟计算**的数据流抽象，通过管道化操作处理数据，不会一次性将所有数据加载到内存。

**创建方式：**

```java
// 1. 通过集合（最常用）
List<String> list = Arrays.asList("a", "b", "c");
Stream<String> stream1 = list.stream();    // 顺序流
Stream<String> stream2 = list.parallelStream(); // 并行流

// 2. 通过数组
String[] arr = {"a", "b", "c"};
IntStream stream3 = Arrays.stream(arr);
IntStream stream4 = IntStream.of(1, 2, 3);

// 3. 通过 Stream.of 静态工厂
Stream<String> stream5 = Stream.of("a", "b", "c");
Stream<Integer> stream6 = Stream.iterate(0, n -> n + 2).limit(10);  // 无限等差数列

// 4. 通过 Stream.generate 无限流
Stream<Double> stream7 = Stream.generate(Math::random).limit(5);

// 5. 基本类型专用流（避免装箱/拆箱）
IntStream intStream = IntStream.rangeClosed(1, 100);  // [1, 100]
LongStream longStream = LongStream.empty();
DoubleStream doubleStream = DoubleStream.builder().add(1.0).add(2.0).build();

// 6. 通过 String.chars()（字符流）
IntStream charStream = "hello".chars();  // 返回 IntStream（字符 ASCII 码）
charStream.forEach(c -> System.out.print((char) c + " "));  // h e l l o
```

> **核心概念：Stream 不是数据结构**，它不存储元素，只是从源（如集合、数组、文件）传输元素，并在管道中通过操作函数（map、filter、reduce 等）进行处理。

### 12.2.2 中间操作（Intermediate Operations）

中间操作返回一个新的 Stream，**都是惰性的**（lazy）——直到遇到终止操作时才会真正执行，这种机制叫做**延迟执行（Lazy Evaluation）**。

| 操作 | 方法签名 | 说明 |
|------|---------|------|
| `filter` | `Stream<T> filter(Predicate<? super T> predicate)` | 按条件过滤 |
| `map` | `<R> Stream<R> map(Function<? super T, ? extends R> mapper)` | 元素转换 |
| `flatMap` | `<R> Stream<R> flatMap(Function<? super T, ? extends Stream<? extends R>> mapper)` | 扁平化映射 |
| `distinct` | `Stream<T> distinct()` | 去重（依赖 equals） |
| `sorted` | `Stream<T> sorted()` / `sorted(Comparator<? super T> comparator)` | 排序 |
| `limit` | `Stream<T> limit(long maxSize)` | 截取前 N 个 |
| `skip` | `Stream<T> skip(long n)` | 跳过前 N 个 |
| `takeWhile` | `Stream<T> takeWhile(Predicate<? super T> predicate)` | Java 9+，条件满足时取 |
| `dropWhile` | `Stream<T> dropWhile(Predicate<? super T> predicate)` | Java 9+，条件满足时丢 |
| `peek` | `Stream<T> peek(Consumer<? super T> action)` | 调试用，窥视每个元素 |

```java
// 常用中间操作示例
List<Student> students = getStudents();

List<String> names = students.stream()
    .filter(s -> s.getScore() >= 60)        // 过滤
    .map(Student::getName)                   // 映射
    .distinct()                              // 去重
    .sorted(Comparator.comparingInt(String::length).reversed()) // 排序
    .skip(1)                                 // 跳过第一个
    .limit(10)                               // 取前10
    .collect(Collectors.toList());

// flatMap：将每个元素展开成多个元素
List<String> words = Arrays.asList("hello world", "java stream");
List<String> letters = words.stream()
    .flatMap(s -> Arrays.stream(s.split("\\s+")))  // 拆分成单词流
    .distinct()
    .sorted()
    .collect(Collectors.toList());
// 结果: [hello, java, stream, world]
```

### 12.2.3 终止操作（Terminal Operations）

终止操作触发管道的实际执行，每个 Stream **只能有一个终止操作**，执行后 Stream 消费完毕，不能再使用。

**分类汇总：**

| 分类 | 方法 | 说明 |
|------|------|------|
| 聚合 | `count()`, `max()`, `min()`, `sum()` (基本类型流) | 基本统计 |
| 规约 | `reduce()`（三版本） | 将元素合并为单一值 |
| 收集 | `collect()` | 收集到集合/Map/字符串等 |
| 遍历 | `forEach()`, `forEachOrdered()` | 遍历（并行时不保证顺序） |
| 匹配 | `anyMatch()`, `allMatch()`, `noneMatch()` | 短路匹配 |
| 查找 | `findFirst()`, `findAny()` | 返回 Optional |
| 转数组 | `toArray()` | 转为数组 |

```java
// reduce 入门：三版本
List<Integer> nums = Arrays.asList(1, 2, 3, 4, 5);

// 版本1：无初始值，返回 Optional
Optional<Integer> sum1 = nums.stream().reduce((a, b) -> a + b); // Optional[15]

// 版本2：有初始值，返回具体类型
Integer sum2 = nums.stream().reduce(0, Integer::sum);  // 15

// 版本3：带 combiner（用于并行）
Integer sum3 = nums.parallelStream().reduce(
    0,                    // identity
    Integer::sum,          // accumulator
    Integer::sum           // combiner（合并各分片结果）
);
```

### 12.2.4 常用收集器（Collectors）

`collect()` 是最强大的终止操作，Collectors 提供了丰富的预定义收集器：

```java
List<String> list = students.stream()
    .map(Student::getName)
    .collect(Collectors.toList());        // → List
    // .collect(Collectors.toSet())        // → Set（去重）
    // .collect(Collectors.toCollection(LinkedList::new))  // 指定集合类型

// 分组
Map<String, List<Student>> byClass = students.stream()
    .collect(Collectors.groupingBy(Student::getClassName));
// 多级分组
Map<String, Map<String, List<Student>>> byClassAndGender = students.stream()
    .collect(Collectors.groupingBy(
        Student::getClassName,
        Collectors.groupingBy(Student::getGender)
    ));

// 分区（按布尔值分为两组）
Map<Boolean, List<Student>> passed = students.stream()
    .collect(Collectors.partitioningBy(s -> s.getScore() >= 60));

// 字符串拼接
String names = students.stream()
    .map(Student::getName)
    .collect(Collectors.joining(", ", "[", "]"));
// 结果: [alice, bob, charlie]

// 统计（一次性得到各种统计值）
IntSummaryStatistics stats = students.stream()
    .collect(Collectors.summarizingInt(Student::getScore));
System.out.println(stats.getAverage());  // 平均分
System.out.println(stats.getMax());       // 最高分
System.out.println(stats.getMin());       // 最低分

// 一般化收集（下游收集器）
Map<String, Long> countByClass = students.stream()
    .collect(Collectors.groupingBy(
        Student::getClassName,
        Collectors.counting()  // 下游收集器
    ));

// 映射 + 收集（等价 map 再收集）
Set<String> namesSet = students.stream()
    .map(Student::getName)
    .collect(Collectors.toSet());
```

---

## 12.3 并行流与性能优化

### 12.3.1 parallelStream 基础

Java 8 引入了并行流，通过 `parallelStream()` 或 `stream().parallel()` 启用，自动将数据拆分成多个块，在多核 CPU 上并行处理。

**原理：Fork/Join 框架**

```
主线程（Main）
    ↓ 分叉（fork）
[块1] [块2] [块3] [块4]
    ↓ 计算
[块1] [块2] [块3] [块4]
    ↓ 合并（join）
主线程（Main）
```

```java
// 顺序流 vs 并行流
long start = System.nanoTime();
int sum1 = IntStream.rangeClosed(1, 1_000_000)
    .sum();  // 顺序
long end = System.nanoTime();
System.out.println("顺序: " + (end - start) + " ns");

long start2 = System.nanoTime();
int sum2 = IntStream.rangeClosed(1, 1_000_000)
    .parallel()  // 并行
    .sum();
long end2 = System.nanoTime();
System.out.println("并行: " + (end2 - start2) + " ns");
```

### 12.3.2 何时使用并行流

**适合并行的场景：**

- 数据量较大（>10000 条）
- 操作是 stateless（无状态，不依赖其他元素）
- 运算是 CPU 密集型（非 IO 等待）
- 无序或最终结果与顺序无关（如聚合、过滤）

**不适合并行的场景：**

- 数据量小（并行开销反而更大）
- 有状态的依赖操作（如 `limit`、`findFirst` 短路操作）
- 有顺序要求（需要 `forEachOrdered`）
- 操作本身有同步/锁（如使用共享变量）

```java
// ❌ 错误场景：并行流 + 有状态操作
// 以下代码结果不可靠！
Set<Integer> seen = new HashSet<>();
boolean hasDuplicate = list.parallelStream().anyMatch(e -> !seen.add(e));
// seen.add(e) 在并行环境下有数据竞争，结果不确定

// ✅ 正确做法：顺序流或自定义线程安全逻辑
Set<Integer> seen = ConcurrentHashMap.newKeySet();
boolean hasDuplicate = list.parallelStream().anyMatch(e -> !seen.add(e)); // ConcurrentHashMap线程安全

// ✅ 或者用标准库方法
boolean hasDuplicate = list.stream().distinct().count() != list.size();
```

### 12.3.3 ForkJoinPool 深入

Java 7 引入的 Fork/Join 框架是并行流的后台引擎。默认情况下，并行流使用**公共 ForkJoinPool**：

```java
// 查看默认并行度（= CPU 核心数）
System.out.println(ForkJoinPool.getCommonPoolParallelism());  // 通常 = CPU核心数

// 自定义 ForkJoinPool（用于特定场景）
ForkJoinPool customPool = new ForkJoinPool(8);  // 指定并行度8

List<String> results = customPool.submit(() ->
    list.parallelStream()
        .map(this::heavyComputation)
        .collect(Collectors.toList())
).join();

// ⚠️ 注意：不要将长时间运行的任务提交到公共 ForkJoinPool
// 公共池被所有并行流共享，阻塞会导致其他任务饥饿
```

**自定义线程池替代公共池：**

```java
// 推荐方式：为并行流指定线程池
ExecutorService executor = Executors.newFixedThreadPool(4);

List<Result> results = list.parallelStream()
    .collect(Collectors.collectingAndThen(
        Collectors.toCollection(() ->
            new java.util.Vector<>()  // 线程安全容器收集结果
        ),
        r -> {
            executor.shutdown();
            return r;
        }
    ));

// 更推荐：使用 CompletableFuture（见下）
CompletableFuture<List<Result>> future = list.stream()
    .map(item -> CompletableFuture.supplyAsync(() -> process(item), executor))
    .collect(Collectors.collectingAndThen(Collectors.toList(),
        futures -> futures.stream()
            .map(CompletableFuture::join)
            .collect(Collectors.toList())));
```

### 12.3.4 并行流性能调优技巧

**减少装箱/拆箱：** 基本类型流性能显著优于包装类型流

```java
// ❌ 包装类型装箱开销大
Stream<Integer> boxed = IntStream.rangeClosed(1, 1_000_000)
    .boxed();

// ✅ 基本类型流（无装箱）
int sum = IntStream.rangeClosed(1, 1_000_000)
    .parallel()
    .sum();
```

**使用 `findAny()` 替代 `findFirst()` 允许更多短路优化：**

```java
// 在并行流中，findAny 比 findFirst 有更多优化空间
Optional<String> any = list.parallelStream()
    .filter(s -> s.startsWith("A"))
    .findAny();  // ✅ 并行友好
```

**组合操作顺序调优：**

```java
// 小数据量或最终结果与顺序无关时，调换 filter/map 顺序可能减少后续计算量
list.stream()
    .filter(x -> x > 0)         // 先过滤，减少 map 处理量
    .map(Math::sqrt)
    ...

// limit 在 filter 之前 vs 之后
list.stream()
    .filter(x -> x > 100)       // 大量过滤后再 limit
    .limit(10)
    ...

// 在 filter 前先 limit（短路）
list.stream()
    .limit(1000)                // 先限制规模
    .filter(x -> x > 100)
    .map(...)
    ...
// 选择取决于数据分布，需实测
```

**减少中间操作的副作用：** 避免在 Lambda 中产生共享变量修改

```java
// ❌ 副作用：共享变量竞争
List<String> results = Collections.synchronizedList(new ArrayList<>());
list.parallelStream().forEach(e -> results.add(process(e)));

// ✅ 无副作用的收集
List<String> results = list.parallelStream()
    .map(this::process)
    .collect(Collectors.toList());
```

---

## 12.4 Optional 最佳实践

### 12.4.1 Optional 基础

`Optional<T>` 是 Java 8 引入的用于替代 `null` 引用的类型安全的容器，代表**值存在或不存在**两种状态，避免空指针异常（NPE）。

**创建 Optional：**

```java
Optional<String> present = Optional.of("hello");           // 非空，不能为 null
Optional<String> nullable = Optional.ofNullable(null);     // 可为 null
Optional<String> empty = Optional.empty();                // 空
```

### 12.4.2 常用方法速查

| 方法 | 说明 |
|------|------|
| `get()` | 获取值，为空则抛异常 |
| `orElse(T other)` | 为空则返回默认值 |
| `orElseGet(Supplier<? extends T> other)` | 为空则调用 Supplier（延迟计算） |
| `orElseThrow(Supplier<? extends X> exceptionSupplier)` | 为空则抛指定异常 |
| `isPresent()` | 判断是否存在 |
| `ifPresent(Consumer<? super T> action)` | 存在则执行 Consumer |
| `isEmpty()` | 判断不存在（Java 11+） |
| `filter(Predicate<? super T> predicate)` | 满足条件返回自身，否则返回空 |
| `map(Function<? super T, ? extends U> mapper)` | 存在则转换，否则返回空 |
| `flatMap(Function<? super T, Optional<U>> mapper)` | 存在则映射（返回 Optional），否则空 |
| `stream()` | 转为 Stream（Java 9+，空则返回空流） |
| `or(Supplier<? extends Optional<? extends T>> supplier)` | Java 9+，链式备选 |

### 12.4.3 链式调用实战

```java
// 典型场景：安全获取嵌套属性
// ❌ 传统方式（深层嵌套 NPE 风险）
String city = user.getAddress().getCity().getName();  // 每层都可能 NPE

// ✅ Optional 链式
String city = Optional.ofNullable(user)
    .map(User::getAddress)
    .map(Address::getCity)
    .map(City::getName)
    .orElse("未知");

// flatMap：处理返回 Optional 的方法（避免 Optional<Optional<T>>）
public Optional<String> findPhoneNumber(User user) { ... }

Optional<String> phone = Optional.ofNullable(user)
    .flatMap(User::getPhoneNumber);  // ✅ 返回 Optional<String>
    // 如果用 map，会得到 Optional<Optional<String>>
```

### 12.4.4 orElse vs orElseGet

**关键区别：默认值是否被计算**

```java
private String getDefault() {
    System.out.println("getDefault() 被调用！");
    return "默认城市";
}

// orElse：无论是否为空，默认值都会被求值
Optional<String> opt = Optional.of("北京");
String r1 = opt.orElse(getDefault());  // 打印 "getDefault() 被调用！"

// orElseGet：如果值存在，Supplier 不调用（延迟）
String r2 = opt.orElseGet(this::getDefault);  // 不打印，方法不被调用

// ✅ 最佳实践：使用 orElseGet 处理计算量大的默认值
String result = userOpt.orElseGet(() -> computeDefaultUser());
// ❌ 不要用 orElse(result) 其中 result 是 new Object()（每次都创建）
```

### 12.4.5 常见坑与最佳实践

**坑 1：Optional 不等于判空**

```java
// ❌ 错误用法：Optional 用作字段类型（序列化问题）
public class User {
    private Optional<String> nickname;  // 反序列化困难，不推荐
}
// ✅ 正确做法：普通字段 + JSR-305 @Nullable 注解
public class User {
    private String nickname;  // 普通字段，可为 null
}

// 使用时：
Optional.ofNullable(user.getNickname()).ifPresent(...);
```

**坑 2：map 后继续链式 filter**

```java
Optional<User> userOpt = Optional.empty();

// filter 清除后为空
Optional<User> filtered = userOpt
    .filter(u -> u.getAge() > 18);  // 结果：Optional.empty

// 链式继续不会自动恢复，需要注意
filtered.map(User::getName).orElse("匿名");
```

**坑 3：在 JSON 序列化中使用 Optional**

```java
// 使用 Jackson 序列化 Optional 字段会序列化为 {"nickname": null}
// 而不是省略该字段，需要自定义配置
ObjectMapper mapper = new ObjectMapper();
mapper.registerModule(new JavaTimeModule());
// 或使用 @JsonSerialize(as = String.class) 等注解

// 推荐：永远不要在 API 响应 DTO 中使用 Optional
public class UserDTO {
    private String nickname;  // 直接 String，null 就 null
}
```

**最佳实践总结：**

```java
// 1. 用 Optional 替代 null 判断链
String name = Optional.ofNullable(user)
    .map(User::getName)
    .orElse("游客");

// 2. 集合返回 Optional 而非 null
public Optional<User> findById(Long id) {
    return Optional.ofNullable(cache.get(id));
    // 而不是 return cache.get(id); // 可能返回 null
}

// 3. Optional 作为方法参数（需权衡，过度使用反而复杂）
// ✅ 适合：需要明确表示"值可选"的场景
public Optional<String> findNickname(Long userId) { ... }

// ❌ 不适合：强制使用者做 Optional 判断，增加复杂度
// public void process(Optional<String> nickname) { ... }

// 4. Optional 的工业级用法：or 方法链（Java 9+）
String result = Optional.ofNullable(primarySource)
    .or(() -> Optional.ofNullable(fallbackSource))
    .or(() -> Optional.of(defaultValue))
    .orElseThrow(() -> new IllegalStateException("No source available"));

// 5. stream() 将 Optional 转为流（Java 9+）
List<String> names = users.stream()
    .flatMap(u -> u.getNickname().stream())  // Optional<String> 转 Stream<String>
    .collect(Collectors.toList());

// 6. ifPresentOrElse（Java 9+）
userOpt.ifPresentOrElse(
    u -> System.out.println("找到用户: " + u.getName()),
    () -> System.out.println("用户不存在")
);
```

---

## 12.5 DateTime API

### 12.5.1 旧版 Date 的问题

Java 8 之前使用的 `java.util.Date` 和 `java.util.Calendar` 有严重的设计缺陷：

```java
// ❌ 旧版 Date 的问题
Date date = new Date(2024, 1, 1);  // ❌ Month 从 0 开始，Year 是年份偏移量
// 实际：Date(124, 1, 1) 表示 2024+1900=3924年！
date.setYear(2024 - 1900);  // 手动偏移，坑！

// ❌ Calendar 月份也是从 0 开始，容易出错
Calendar cal = Calendar.getInstance();
cal.set(2024, Calendar.JANUARY, 1);  // 手动指定 January = 0

// ❌ Date 是可变对象，不是线程安全的
Calendar cal = Calendar.getInstance();
cal.setTime(new Date());  // 修改了传入的 Date 对象

// ❌ 无法表示"不带时区的时间"
```

### 12.5.2 LocalDateTime（本地日期时间）

```java
import java.time.*;

// 1. 获取当前时间
LocalDateTime now = LocalDateTime.now();  // 2024-04-28T20:37:00.123

// 2. 构建指定时间
LocalDateTime dt = LocalDateTime.of(2024, 4, 28, 20, 30);
LocalDateTime dt2 = LocalDateTime.of(2024, 4, 28, 20, 30, 45, 123456789);

// 3. 从字符串解析
LocalDateTime parsed = LocalDateTime.parse("2024-04-28T20:30:00");
LocalDateTime parsed2 = LocalDateTime.parse("2024-04-28 20:30:00",
    DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

// 4. 常用操作
LocalDateTime nextWeek = now.plusWeeks(1);
LocalDateTime lastMonth = now.minusMonths(1);
LocalDateTime newYear = now.withDayOfYear(1).withMonth(1).withHour(0).withMinute(0);

// 5. 提取各部分
int year = now.getYear();         // 2024
Month month = now.getMonth();     // APRIL
int day = now.getDayOfMonth();    // 28
int hour = now.getHour();          // 20

// 6. 格式化
DateTimeFormatter fmt = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
String str = now.format(fmt);  // "2024-04-28 20:37:00"

// 7. LocalDate 和 LocalTime
LocalDate date = now.toLocalDate();  // 2024-04-28
LocalTime time = now.toLocalTime();  // 20:37:00.123
```

### 12.5.3 ZonedDateTime（带时区）

```java
// 1. 当前时区时间
ZonedDateTime nowInShanghai = ZonedDateTime.now();
ZonedDateTime nowInTokyo = ZonedDateTime.now(ZoneId.of("Asia/Tokyo"));

// 2. 带时区的指定时间（用于跨时区场景）
ZonedDateTime meeting = ZonedDateTime.of(
    LocalDateTime.of(2024, 4, 28, 9, 0),
    ZoneId.of("America/New_York")
);
System.out.println(meeting);  // 2024-04-28T09:00-04:00[America/New_York]

// 3. 时区转换
ZonedDateTime tokyoTime = ZonedDateTime.now(ZoneId.of("Asia/Tokyo"));
ZonedDateTime shanghaiTime = tokyoTime.withZoneSameInstant(ZoneId.of("Asia/Shanghai"));
System.out.println(shanghaiTime);  // 时区相同，时间相同（时区偏移不同）

// 4. Instant（UTC 时间戳）
Instant nowUtc = Instant.now();
long epochMilli = nowUtc.toEpochMilli();  // 毫秒时间戳（与 JDBC / JS Date 一致）
System.out.println(nowUtc);  // 2024-04-28T12:37:00.123Z

// 5. Instant ↔ LocalDateTime 互转
LocalDateTime local = LocalDateTime.of(2024, 4, 28, 20, 30);
Instant instant = local.atZone(ZoneId.systemDefault()).toInstant();  // Local → Instant
LocalDateTime back = instant.atZone(ZoneId.systemDefault()).toLocalDateTime();  // Instant → Local

// 6. Duration 和 Period
Duration duration = Duration.between(start, end);  // 时间段（秒/毫秒）
Period period = Period.between(startDate, endDate);  // 日期段（天/月/年）
```

### 12.5.4 格式化（DateTimeFormatter）

```java
import java.time.format.*;

// 预置格式
String s1 = now.format(DateTimeFormatter.ISO_LOCAL_DATE);          // 2024-04-28
String s2 = now.format(DateTimeFormatter.ISO_LOCAL_TIME);          // 20:37:00
String s3 = now.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);     // 2024-04-28T20:37:00

// 自定义格式
DateTimeFormatter f1 = DateTimeFormatter.ofPattern("yyyy/MM/dd HH:mm");
DateTimeFormatter f2 = DateTimeFormatter.ofPattern("yyyy年M月d日 HH:mm:ss E");
String s4 = now.format(f2);  // "2024年4月28日 20:37:00 周日"

// 本地化格式
DateTimeFormatter localized = DateTimeFormatter.ofLocalizedDateTime(FormatStyle.MEDIUM);
String s5 = now.format(localized);  // "2024-4-28 下午8:37:00"（中文环境）

// 解析（带时区信息）
ZonedDateTime zdt = ZonedDateTime.parse("2024-04-28T20:30+08:00[Asia/Shanghai]", 
    DateTimeFormatter.ISO_ZONED_DATE_TIME);

// 常见格式符
// y=年 M=月 d=日 H=24小时制 h=12小时制 m=分 s=秒 S=毫秒 a=上午/下午 E=星期 z=时区名
```

### 12.5.5 与旧 API 互转

```java
// Date → LocalDateTime
Date date = new Date();
Instant instant = date.toInstant();
LocalDateTime ldt = LocalDateTime.ofInstant(instant, ZoneId.systemDefault());

// LocalDateTime → Date
LocalDateTime ldt2 = LocalDateTime.now();
Instant instant2 = ldt2.atZone(ZoneId.systemDefault()).toInstant();
Date date2 = Date.from(instant2);

// Timestamp → LocalDateTime（JDBC 常用）
Timestamp ts = new Timestamp(System.currentTimeMillis());
LocalDateTime ldt3 = ts.toLocalDateTime();

// LocalDate → java.sql.Date
LocalDate ld = LocalDate.now();
java.sql.Date sqlDate = java.sql.Date.valueOf(ld);  // ✅ 相互转换
LocalDate back = sqlDate.toLocalDate();

// Instant 替代 System.currentTimeMillis()
long ms = Instant.now().toEpochMilli();  // 替代 System.currentTimeMillis()
Instant fromEpoch = Instant.ofEpochMilli(ms);
```

---

## 12.6 Java 14-21 新特性

### 12.6.1 Record 记录类型（Java 14+，正式版 Java 16）

**Record** 是一种新的类声明形式，用于创建不可变的数据载体类（Data Carrier）。编译器自动生成 `equals()`、`hashCode()`、`toString()` 以及构造函数和所有字段的访问方法。

```java
// 传统写法：大量样板代码
public class Point {
    private final int x;
    private final int y;

    public Point(int x, int y) {
        this.x = x;
        this.y = y;
    }

    public int getX() { return x; }
    public int getY() { return y; }

    @Override
    public boolean equals(Object o) { /* 手动实现 */ }
    @Override
    public int hashCode() { /* 手动实现 */ }
    @Override
    public String toString() { /* 手动实现 */ }
}

// ✅ Record 写法：一行顶几十行
public record Point(int x, int y) {}

// 自动生成：构造方法、getX()/getY()、equals/hashCode/toString
Point p = new Point(1, 2);
System.out.println(p.x());   // 1，访问方法名 = 字段名（不是 getX）
System.out.println(p);       // Point[x=1, y=2]
```

**Record 可以添加额外成员（方法、静态字段、构造函数扩展）：**

```java
public record Range(int min, int max) {
    // 紧凑构造函数（编译器生成主构造函数后自动调用）
    public Range {
        if (min > max) throw new IllegalArgumentException("min > max");
    }

    // 可以添加方法
    public int span() {
        return max - min;
    }

    // 静态成员
    public static Range ALL = new Range(Integer.MIN_VALUE, Integer.MAX_VALUE);

    // 静态工厂方法
    public static Range of(int a, int b) {
        return new Range(Math.min(a, b), Math.max(a, b));
    }
}
```

**Record 的限制：**

- 隐式 `final`，不能继承其他类（但可以实现接口）
- 字段隐式 `final`，不可修改（immutable）
- 不能声明实例字段（只能是构造函数的参数）
- 不能有实例初始化器（但可以有静态初始化器）

**Record 应用于模式匹配（Java 16+）：**

```java
// instanceof + record（Java 16+ Pattern Matching for instanceof）
Object obj = new Point(10, 20);

// 旧写法
if (obj instanceof Point) {
    Point p = (Point) obj;
    System.out.println(p.x() + p.y());
}

// ✅ 新写法：模式匹配（可以在同一行内完成类型检查 + 绑定变量）
if (obj instanceof Point(int x, int y)) {
    System.out.println(x + y);  // x, y 直接可用，无需转型
}
```

### 12.6.2 Sealed Classes 密封类（Java 17+，正式版 Java 17）

**Sealed Classes** 用于限制一个类/接口的直接子类数量，只有被允许的子类可以继承它。用于表达**有限类型联合**的思想。

```java
// 密封类：只允许特定子类继承
public sealed class Shape permits Circle, Rectangle, Triangle {
    // Shape 只能是 Circle、Rectangle 或 Triangle 的父类
}

// 具体子类：可以声明为 final、sealed 或 non-sealed
final class Circle extends Shape { double radius; }
sealed class Rectangle extends Shape permits Square { double width, height; }
non-sealed class Triangle extends Shape { double base, height; }

// Square 作为 Rectangle 的 sealed 子类
sealed class Square extends Rectangle permits — { double side; }  // permits 指向无子类
```

**使用场景：配合 `instanceof` 模式匹配实现穷举（Exhaustive Switch）：**

```java
// 穷举式 switch（编译器保证覆盖所有情况）
double area(Shape s) {
    return switch (s) {
        case Circle c    -> Math.PI * c.radius() * c.radius();
        case Rectangle r -> r.width() * r.height();
        case Triangle t  -> 0.5 * t.base() * t.height();
        // 编译器知道没有其他子类，不需要 default
    };
}
```

### 12.6.3 Switch 表达式（Java 14+，正式版 Java 21）

**Switch 表达式**从 Java 14 开始正式可用，支持**箭头语法**和**返回值**，并支持**模式匹配**。

```java
// 传统 switch 语句
int days = 0;
switch (month) {
    case 1: case 3: case 5: case 7:
    case 8: case 10: case 12:
        days = 31; break;
    case 4: case 6: case 9: case 11:
        days = 30; break;
    case 2:
        days = 28; break;
    default:
        days = -1;
}

// ✅ 新 Switch 表达式（箭头语法，break 不再需要）
int days = switch (month) {
    case 1, 3, 5, 7, 8, 10, 12 -> 31;
    case 4, 6, 9, 11 -> 30;
    case 2 -> 28;
    default -> -1;
};

// 箭头语法支持代码块
String result = switch (status) {
    case PENDING -> {
        System.out.println("处理中...");
        yield "pending";  // Java 14 yield 关键字返回值
    }
    case DONE -> "completed";
    case FAILED -> {
        logError("Failed!");
        yield "failed";
    }
};
```

**在箭头分支中使用代码块并使用 `yield`：**

```java
// yield vs return：在 switch 表达式块中使用 yield 返回值
int score = switch (grade) {
    case 'A' -> 100;
    case 'B' -> {
        int bonus = hasExtraCredit ? 5 : 0;
        yield 90 + bonus;  // 在 {} 块内必须用 yield
    }
    case 'C' -> 70;
    default -> {
        throw new IllegalArgumentException("Invalid grade: " + grade);
    }
};
```

### 12.6.4 Pattern Matching for instanceof（Java 16+，正式版 Java 16）

```java
// 旧写法：双重复
if (obj instanceof String) {
    String s = (String) obj;  // 需要强制转型
    System.out.println(s.length());
}

// ✅ Java 16+：类型模式，绑定变量自动转换
if (obj instanceof String s) {
    System.out.println(s.length());  // s 已经转型，直接使用
}

// ✅ 结合 && 逻辑
if (obj instanceof String s && s.length() > 5) {
    System.out.println(s.toUpperCase());
}

// ✅ 在 lambda 表达式中（Java 21 preview → Java 22 GA）
Object handler = (String s) -> s.length();
// 类似地可用于 switch
String description = switch (obj) {
    case Integer i -> "int: " + i;
    case String s && s.length() > 10 -> "long string: " + s.length();
    case String s -> "string: " + s;
    case null -> "null";
    default -> "unknown";
};
```

### 12.6.5 虚拟线程（Virtual Threads / Project Loom，Java 21 GA）

**虚拟线程**是 Java 21 正式引入的轻量级线程实现，大幅降低并发编程成本。与传统线程（平台线程）相比，虚拟线程占用极少内存，可轻松创建数百万个。

```java
// 传统线程创建方式
Thread t = new Thread(() -> {
    System.out.println("Hello from platform thread");
});
t.start();

// ✅ 虚拟线程创建
Thread.startVirtualThread(() -> {
    System.out.println("Hello from virtual thread");
});

// 或使用 Thread.ofVirtual().start(...)
Thread virtual = Thread.ofVirtual().start(() -> System.out.println("virtual!"));
virtual.join();

// 虚拟线程工厂
ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();

// 使用虚拟线程执行大量任务（传统方式 OOM，虚拟线程轻松处理）
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 1_000_000).forEach(i -> {
        executor.submit(() -> {
            // 每个任务一个虚拟线程，轻量到可以创建百万级
            Thread.sleep(Duration.ofSeconds(1));
            return i;
        });
    });
}

// 虚拟线程适合 IO 密集型任务，不适合 CPU 密集型
// CPU 密集型仍建议使用线程池 + 分区处理
```

**虚拟线程 vs 平台线程关键对比：**

| 维度 | 平台线程 | 虚拟线程 |
|------|---------|---------|
| 创建成本 | 高（OS 线程，约 1MB 栈） | 极低（heap 分配，约 200B-1KB） |
| 数量上限 | 数百~数千 | 数百万 |
| 阻塞行为 | 阻塞 OS 线程 | 挂载（Mount）到平台线程，释放 |
| 使用场景 | CPU 密集型 | IO 密集型（HTTP、数据库、消息） |

> **注意**：虚拟线程仍然依赖 OS 线程运行（不放弃线程模型），但一个平台线程可以承载大量虚拟线程。虚拟线程被阻塞时（如等待 IO），会自动"卸载"（Unmount），让平台线程去执行其他虚拟线程。

**虚拟线程最佳实践：**

```java
// ✅ 使用虚拟线程的正确姿势
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<String>> futures = IntStream.range(0, 10_000)
        .mapToObj(i -> executor.submit(() -> callHttpApi(i)))
        .collect(Collectors.toList());

    for (var f : futures) {
        System.out.println(f.get());
    }
}

// ❌ 错误的做法：虚拟线程中使用 ThreadLocal 共享可变状态
ThreadLocal<MyContext> context = new ThreadLocal<>();
// 虚拟线程会反复创建销毁，ThreadLocal 不会再被自动清理
// 解决方案：使用 Scoped Values（Java 21+），或注意在使用完毕后调用 remove()

// ✅ 虚拟线程中使用 ThreadPoolExecutor 手动管理（不推荐 newFixedThreadPool）
// 虚拟线程不绑定平台线程，手动指定线程数没有意义，反而增加复杂性
```

---

## 12.7 常见面试题

### Q1：Lambda 与匿名内部类的区别？

| 维度 | Lambda | 匿名内部类 |
|------|--------|-----------|
| 语法 | 更简洁 | 较冗长 |
| `this` 引用 | 指向包围方法所属类 | 指向匿名内部类自身 |
| 编译方式 | 生成 `invokedynamic` 指令（Java 8+） | 生成单独的 `.class` 文件 |
| 变量捕获 | 只能引用 effectively final 变量 | 可以修改外部变量（需为 final） |
| 可访问性 | 无法访问默认方法（需显式声明接口类型） | 可访问接口默认方法 |

```java
public class LambdaVsAnon {
    interface Greeting { void greet(); }

    public void test() {
        String name = "World";
        Greeting lambda = () -> System.out.println("Hello " + name);
        Greeting anon = new Greeting() {
            @Override
            public void greet() {
                System.out.println("Hello " + name);  // 效果相同
                // 但 this 指向不同：
                // lambda 中 this → LambdaVsAnon 实例
                // anon 中 this → 匿名内部类实例
            }
        };
    }
}
```

### Q2：Stream 的惰性执行原理？

Stream 的中间操作返回新的 Stream，所有操作构成**管道（Pipeline）**，只有在调用终止操作时，才从数据源开始**逐个元素**向下流动，每个元素依次经过每个中间操作（类似于流水线），最终由终止操作触发。这种机制使得：

1. **短路操作**（`findFirst`、`anyMatch`）可以在满足条件时立即停止处理
2. **减少不必要的计算**（`limit` 等可以提前截断）
3. **只需一次遍历**（不像集合的连续 filter/map 需要多次遍历）

```java
// 这行代码不会立即执行任何操作（惰性）
list.stream()
    .filter(s -> { System.out.println("filter: " + s); return s.length() > 3; })
    .map(s -> { System.out.println("map: " + s); return s.toUpperCase(); })
    .limit(2)  // 短路
    .forEach(System.out::println);  // 终止操作触发执行

// 输出示例：
// filter: a
// filter: abc      ← 被过滤
// filter: abcd    → 通过 filter
// map: ABCD        → 通过 map
// ABCD             → 打印
// filter: xyz      → 第二元素
// filter: xy
// filter: xyzw     → 通过 filter
// map: XYZW        → 通过 map
// XYZW             → 打印
// (已满足 limit(2)，停止处理)
```

### Q3：parallelStream 的线程安全问题

```java
// ❌ 常见错误：并发修改共享集合
List<String> list = new ArrayList<>();
list.parallelStream().forEach(e -> list.add(e));  // 数据竞争！

// ✅ 正确做法：使用线程安全集合 或 reduce/collect
List<String> safe = list.parallelStream()
    .map(this::transform)
    .collect(Collectors.toList());  // 不涉及共享变量

// ✅ 或使用 ConcurrentHashMap 等
ConcurrentHashMap<String, Integer> counter = new ConcurrentHashMap<>();
list.parallelStream().forEach(e -> 
    counter.merge(e, 1, Integer::sum)  // 线程安全合并
);
```

### Q4：Optional 的正确使用场景与误区

**误区 1：过度使用作为字段**

```java
// ❌ 反模式：Optional 作为字段
class User { Optional<String> phone; }  // 序列化复杂，滥用Optional

// ✅ 正确做法
class User { String phone; }  // 普通字段，可为null
```

**误区 2：用 Optional 替代 null 判断**

```java
// 简单场景不必用 Optional
String name = user != null ? user.getName() : null;  // 简单明了

// 复杂链式场景用 Optional
String name = Optional.ofNullable(user)
    .map(User::getAddress)
    .map(Address::getCity)
    .map(City::getName)
    .orElse("未知");
```

### Q5：Java 8 日期时间 API 与旧 API 的区别？

| 特性 | 旧 API (Date/Calendar) | 新 API (DateTime) |
|------|----------------------|-----------------|
| 线程安全 | 否（Date/Calendar 都可变） | 是（所有类都是线程安全） |
| API 清晰度 | 月份从 0 开始，混乱 | 月份从 1 开始，符合直觉 |
| 时区处理 | 复杂（TimeZone 类） | 原生支持（ZonedDateTime） |
| 时间运算 | 通过 Calendar，繁琐 | 直接加/减（plusDays/minusHours） |
| 不可变 | Date 可变 | 所有类型不可变（安全并发） |

### Q6：Record 和普通类的区别？适合哪些场景？

```java
// Record 适合：不可变数据载体
record UserDTO(String name, int age, String email) {}

// 普通类适合：需要可变状态、业务逻辑、继承体系
class User {
    private String name;
    private int age;
    private List<Order> orders;  // 有复杂业务逻辑，普通类更合适
}
```

---

## 本章小结

本章系统梳理了 Java 8 至 Java 21 的核心新特性，重点包括：

| 知识点 | 关键内容 |
|--------|---------|
| **Lambda 表达式** | 语法、函数式接口 `@FunctionalInterface`、方法引用 `::`、外部变量 effectively final 限制 |
| **Stream API** | 创建方式（集合/数组/工厂方法）、中间操作（filter/map/flatMap/sorted/distinct/limit）、终止操作（collect/reduce/forEach/match/find）、惰性执行原理、常用收集器（groupingBy/partitioningBy/joining） |
| **并行流** | ForkJoinPool 原理、parallelStream 使用场景、线程安全集合、避免共享状态副作用 |
| **Optional** | orElse/orElseGet/orElseThrow、map/flatMap/filter 链式调用、Java 9+ 新方法（or/ifPresentOrElse/stream） |
| **DateTime API** | LocalDateTime/ZonedDateTime/Instant、格式化 DateTimeFormatter、时区转换、与旧 API 互转 |
| **Java 14-21 新特性** | Record（数据载体 + 模式匹配）、Sealed Classes（有限继承 + 穷举 switch）、Switch 表达式（箭头语法 + yield）、Pattern Matching for instanceof、虚拟线程（Project Loom，轻量并发） |

**实践建议：**
- Lambda 和 Stream 是 Java 8+ 开发的基础工具链，务必熟练掌握链式调用与惰性执行
- 并行流不要滥用——数据量小、有状态或有顺序要求时用顺序流更安全
- Optional 是减少 NPE 的利器，但不要滥用为字段类型或过度嵌套
- DateTime API 已经成熟稳定，新项目务必使用，不要再碰旧 `Date`/`Calendar`
- Java 17+ 的新语法（Record、Sealed、Switch表达式）在金融、电商等复杂系统中有很好的应用价值
- 虚拟线程是 Java 21 的重磅特性，IO 密集型服务（微服务、爬虫、消息处理）迁移后可获得极高的并发吞吐量

---

**下一章：Ch13 - Spring/Spring Boot核心**