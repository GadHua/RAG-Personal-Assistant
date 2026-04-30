# Ch05 - 泛型与类型系统

## 5.1 泛型概述

### 什么是泛型

泛型：把**类型参数化**，在编译时进行类型检查，避免强制类型转换和运行时 ClassCastException。

### 没有泛型的问题

```java
//没有泛型：只能存 Object
List list = new ArrayList();
list.add("hello");
list.add(123);  //编译不报错
String s = (String) list.get(1);  //运行时 ClassCastException
```

### 使用泛型

```java
//使用泛型：类型安全
List<String> list = new ArrayList<>();
list.add("hello");
//list.add(123);  //编译错误，类型检查
String s = list.get(0);  //无需强转，类型已知
```

### 泛型的优点

1. **编译时类型检查**：提前发现错误，而不是运行时
2. **消除强制类型转换**：`get()` 直接返回目标类型
3. **代码复用**：一套代码适配多种类型

---

## 5.2 泛型类

### 定义与使用

```java
//泛型类：把类型参数放在类名后面
public class Box<T> {
    private T content;
    
    public T getContent() {
        return content;
    }
    
    public void setContent(T content) {
        this.content = content;
    }
}

//使用：指定具体类型
Box<String> stringBox = new Box<>();
stringBox.setContent("Hello");
String content = stringBox.getContent();  //无需强转

Box<Integer> intBox = new Box<>();
intBox.setContent(100);
Integer num = intBox.getContent();
```

### 多个类型参数

```java
public class Pair<K, V> {
    private K key;
    private V value;
    
    public Pair(K key, V value) {
        this.key = key;
        this.value = value;
    }
    
    public K getKey() { return key; }
    public V getValue() { return value; }
}

Pair<String, Integer> pair = new Pair<>("age", 25);
```

### 类型参数的命名习惯

| 字母 | 含义 |
|-----|------|
| T | Type（类型） |
| E | Element（元素） |
| K | Key（键） |
| V | Value（值） |
| N | Number（数字） |
| R | Return（返回类型） |
| S/U/V | 第二、第三、第四类型 |

---

## 5.3 泛型接口

### 定义

```java
public interface Repository<T> {
    void save(T entity);
    T findById(Long id);
    List<T> findAll();
}
```

### 实现方式

**方式1：实现时指定具体类型**

```java
public class UserRepository implements Repository<User> {
    @Override
    public void save(User entity) { }
    
    @Override
    public User findById(Long id) { return null; }
    
    @Override
    public List<User> findAll() { return null; }
}
```

**方式2：实现时保留泛型（仍为泛型类）**

```java
public class GenericRepository<T> implements Repository<T> {
    @Override
    public void save(T entity) { }
    
    @Override
    public T findById(Long id) { return null; }
    
    @Override
    public List<T> findAll() { return null; }
}
```

---

## 5.4 泛型方法

### 基本语法

```java
//泛型方法：修饰符后面加 <T>，返回类型前加类型参数
public static <T> void printArray(T[] array) {
    for (T element : array) {
        System.out.println(element);
    }
}

//调用
String[] strs = {"A", "B", "C"};
Integer[] nums = {1, 2, 3};
printArray(strs);   //自动推断 T 为 String
printArray(nums);   //自动推断 T 为 Integer
```

### 有返回值的泛型方法

```java
public static <T> T getFirst(List<T> list) {
    if (list == null || list.isEmpty()) {
        return null;
    }
    return list.get(0);
}

String first = getFirst(Arrays.asList("A", "B", "C"));
Integer num = getFirst(Arrays.asList(1, 2, 3));
```

### 泛型方法 vs 泛型类

```java
//泛型类：整个类是泛型，类型参数在实例化时指定
class Box<T> { }
Box<String> box = new Box<>();

//泛型方法：方法自己带类型参数，独立于类
class Util {
    public static <T> T convert(Object obj, Class<T> clazz) {
        return clazz.cast(obj);
    }
}
String s = Util.<String>convert("hello", String.class);
//或 String s = Util.convert("hello", String.class); 自动推断
```

---

## 5.5 类型限定（Bounded Type）

### 上限限定

限制类型参数必须是某个类或接口的子类：

```java
//T 必须是 Number 或其子类（Integer, Double, Long 等）
public class NumberBox<T extends Number> {
    private T value;
    
    public T getValue() {
        return value;
    }
    
    public void printValue() {
        //可以直接调用 Number 的方法
        System.out.println("intValue: " + value.intValue());
    }
}

NumberBox<Integer> box1 = new NumberBox<>();  //OK
NumberBox<Double> box2 = new NumberBox<>();    //OK
NumberBox<String> box3 = new NumberBox<>();    //编译错误，String 不是 Number 子类
```

### 多重限定

```java
//T 必须是 Comparable 且 Serializable 的子类
<T extends Comparable & Serializable>
```

### 下限限定（通配符部分讲）

---

## 5.6 通配符

### 无限定通配符 `<?>`

适用于只读操作，不关心具体类型：

```java
public static void printList(List<?> list) {
    for (Object item : list) {
        System.out.println(item);  //只能当 Object 处理
    }
    //list.add("A");  //编译错误，不能添加
}

List<Integer> intList = Arrays.asList(1, 2, 3);
List<String> strList = Arrays.asList("A", "B");
printList(intList);  //OK
printList(strList);  //OK
```

### 上限通配符 `<? extends T>`

适用于**读取**操作，T 或 T 的子类：

```java
//可以读取（返回类型是 T 或其父类）
public static double sumOfList(List<? extends Number> list) {
    double sum = 0;
    for (Number num : list) {  //可以读取为 Number
        sum += num.doubleValue();
    }
    return sum;
}

List<Integer> intList = Arrays.asList(1, 2, 3);
List<Double> dblList = Arrays.asList(1.1, 2.2);
sumOfList(intList);  //OK
sumOfList(dblList);  //OK
```

### 下限通配符 `<? super T>`

适用于**写入**操作，T 或 T 的父类：

```java
//可以写入（写入 T 或其子类）
public static void addNumbers(List<? super Integer> list) {
    list.add(1);     //可以添加 Integer
    list.add(2);     //可以添加 Integer
    //Integer num = list.get(0);  //编译错误，get 返回类型是 Integer 父类
}

List<Number> numList = new ArrayList<>();
List<Object> objList = new ArrayList<>();
addNumbers(numList);  //OK，Number 是 Integer 父类
addNumbers(objList);  //OK，Object 是 Integer 父类
addNumbers(intList);  //OK，List<Integer> 本身
```

### PECS 原则

**Producer Extends, Consumer Super**

- **读取数据**用 `extends`（生产者）
- **写入数据**用 `super`（消费者）

```java
//生产者：用 extends 读取
public static double sum(List<? extends Number> list) {
    double sum = 0;
    for (Number n : list) {  //读取为 Number
        sum += n.doubleValue();
    }
    return sum;
}

//消费者：用 super 写入
public static void addIntegers(List<? super Integer> list) {
    list.add(1);   //写入 Integer
    list.add(2);   //写入 Integer
}
```

---

## 5.7 类型擦除

### 概念

编译时移除所有类型参数信息，替换为**上限**（默认是 Object）：

```java
//源码
public class Box<T> {
    private T content;
    public T getContent() {
        return content;
    }
}

//编译后（类型擦除后）
public class Box {
    private Object content;  //T 被替换为 Object
    public Object getContent() {
        return content;
    }
}
```

### 有上限的类型擦除

```java
//源码
public class NumberBox<T extends Number> {
    private T value;
    public T getValue() {
        return value;
    }
}

//编译后
public class NumberBox {
    private Number value;  //T 被替换为上限 Number
    public Number getValue() {
        return value;
    }
}
```

### 类型擦除的影响

```java
//泛型不能用于基础类型
List<int> list = new ArrayList<>();  //编译错误
List<Integer> list = new ArrayList<>();  //OK

//泛型不能创建泛型数组
T[] arr = new T[10];  //编译错误

//instanceof 不能使用泛型
if (obj instanceof List<String>) { }  //编译错误
if (obj instanceof List<?>) { }      //OK

//静态方法不能引用类类型参数
static T value;  //编译错误

//不能 new 泛型对象
T obj = new T();  //编译错误
```

### 泛型数组的正确创建方式

```java
//方式1：通过反射
public static <T> T[] createArray(Class<T> clazz, int size) {
    return (T[]) java.lang.reflect.Array.newInstance(clazz, size);
}

//方式2：传入已存在的数组
public static <T> T[] toArray(List<T> list, T[] arr) {
    for (int i = 0; i < list.size(); i++) {
        arr[i] = list.get(i);
    }
    return arr;
}
```

---

## 5.8 泛型与重载

### 同名方法可以重载（不同类型参数）

```java
public class Util {
    public static <T> void print(T value) {
        System.out.println("print: " + value);
    }
    
    public static <T> void print(List<T> list) {
        System.out.println("list size: " + list.size());
    }
}
```

### 不能仅通过类型参数重载

```java
//编译错误：两个方法签名相同（类型擦除后）
public class Util {
    public static <T> void process(List<T> list) { }
    public static <T> void process(List<T> list, int flag) { }  //OK，加了参数
}
```

---

## 5.9 泛型与继承

### 子类保留父类泛型

```java
class Parent<T> { }

class Child<T> extends Parent<T> { }  //保留 T

//使用
Child<String> child = new Child<>();
```

### 子类指定父类泛型

```java
class Parent<T> { }

class StringChild extends Parent<String> { }  //指定为 String

//使用
StringChild child = new StringChild();
//Parent<String> parent = child;  //OK
```

### 子类增加类型参数

```java
class Parent<T> { }

class Child<T, V> extends Parent<T> { }  //增加 V

//使用
Child<String, Integer> child = new Child<>();
```

---

## 5.10 桥接方法

类型擦除后，编译器自动生成**桥接方法**保持多态：

```java
//源码
interface Comparable<T> {
    int compareTo(T o);
}

class User implements Comparable<User> {
    @Override
    public int compareTo(User other) {
        return this.name.compareTo(other.name);
    }
}

//编译后（编译器自动生成桥接方法）
class User implements Comparable {
    @Override
    public int compareTo(User other) {  //原始方法
        return this.name.compareTo(other.name);
    }
    
    @Override
    public int compareTo(Object other) {  //桥接方法
        return this.compareTo((User) other);
    }
}
```

---

## 5.11 泛型的典型应用

### 自定义最小堆（泛型类）

```java
public class MinHeap<T extends Comparable<T>> {
    private List<T> data = new ArrayList<>();
    
    public void add(T element) {
        data.add(element);
        siftUp(data.size() - 1);
    }
    
    public T extractMin() {
        T min = data.get(0);
        data.set(0, data.get(data.size() - 1));
        data.remove(data.size() - 1);
        siftDown(0);
        return min;
    }
    
    private void siftUp(int index) {
        while (index > 0) {
            int parent = (index - 1) / 2;
            if (data.get(index).compareTo(data.get(parent)) < 0) {
                Collections.swap(data, index, parent);
                index = parent;
            } else {
                break;
            }
        }
    }
    
    private void siftDown(int index) { /* ... */ }
}
```

### 通用转换器（泛型方法）

```java
public class Converter {
    public static <T, R> List<R> convert(List<T> source, Function<T, R> mapper) {
        List<R> result = new ArrayList<>();
        for (T item : source) {
            result.add(mapper.apply(item));
        }
        return result;
    }
}

//使用
List<String> names = Arrays.asList("Alice", "Bob", "Charlie");
List<Integer> lengths = Converter.convert(names, String::length);
//[5, 3, 7]
```

### 结果缓存（泛型类）

```java
public class MemoizedFetcher<K, V> {
    private Map<K, V> cache = new ConcurrentHashMap<>();
    private Function<K, V> fetcher;
    
    public MemoizedFetcher(Function<K, V> fetcher) {
        this.fetcher = fetcher;
    }
    
    public V get(K key) {
        return cache.computeIfAbsent(key, fetcher);
    }
}

//使用
MemoizedFetcher<String, User> fetcher = new MemoizedFetcher<>(this::loadUser);
User user = fetcher.get("user123");  //第二次调用直接返回缓存
```

---

## 5.12 泛型常见面试题

### Q1：ArrayList<String> 是 ArrayList 的子类吗？

**不是。** `ArrayList<String>` 和 `ArrayList<Integer>` 是两个完全独立的类型，没有继承关系。

```java
ArrayList<String> strList = new ArrayList<>();
ArrayList<Integer> intList = new ArrayList<>();
//strList = intList;  //编译错误
```

### Q2：`<T>` 和 `<?>` 的区别？

`<T>` 是**确定的类型**，可以在代码中使用（如作为返回类型）；`<?>` 是**未知类型**，只用于泛型声明，不能作为具体类型使用。

```java
<T> T getFirst(List<T> list);      //T 是确定的
<?> void print(List<?> list);      //? 是不确定的
```

### Q3：为什么 Collection 保存 Object 而不是 T？

由于类型擦除，运行时无法知道 T 具体是什么，所以用 Object 存储，读取时需要强转或依赖编译器自动插入类型转换。

---

## 📌 本章小结

Ch05 覆盖了 Java 泛型核心知识点：

- **泛型类/接口**：类型参数化，`<T>` 形式
- **泛型方法**：方法级别的泛型，独立于类
- **类型限定**：`extends` 设定上限
- **通配符**：`<? extends T>`（读）、`<? super T>`（写）、PECS 原则
- **类型擦除**：编译时移除泛型信息，替换为 Object 或上限
- **桥接方法**：编译器自动生成，保持多态
- **泛型应用**：最小堆、转换器、缓存等

下一章：**Ch06 - 注解与反射**，运行时操作类结构的能力。
