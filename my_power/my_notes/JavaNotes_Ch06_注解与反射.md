# Ch06 - 注解与反射

## 6.1 注解概述

### 什么是注解

注解（Annotation）是 Java 5 引入的一种**元数据**形式，用于为代码元素（类、方法、字段等）添加额外信息，这些信息可以在编译时、类加载时或运行时被读取和处理。

### 注解 vs 注释

| 区别 | 注释（Comment） | 注解（Annotation） |
|------|----------------|------------------|
| 关键字 | `//` 或 `/** */` | `@Interface` |
| 对代码的影响 | 完全忽略，编译器无视 | 可以被编译器处理、字节码包含、运行时读取 |
| 用途 | 代码说明文档 | 编译检查、代码生成、框架配置、运行时处理 |

---

## 6.2 内置注解（Java 自带）

### 编译检查注解

```java
//@Override：检查方法是否真的重写了父类方法
@Override
public void toString() {
    return "MyClass{}";
}

//@Deprecated：标记已过时的元素，编译器会警告
@Deprecated
public void oldMethod() {
    System.out.println("不要调用我");
}

//@SuppressWarnings：抑制编译器警告
@SuppressWarnings("unchecked")
public void rawType() {
    List list = new ArrayList();  //警告被抑制
}

//@FunctionalInterface：标记函数式接口（单抽象方法）
@FunctionalInterface
public interface Converter<T, R> {
    R convert(T input);
}
```

### 元注解（注解的注解）

```java
//@Retention：注解保留到什么阶段
@Retention(RetentionPolicy.SOURCE)   //仅源码，编译时丢弃
@Retention(RetentionPolicy.CLASS)   //编译时保留，运行时丢弃（默认）
@Retention(RetentionPolicy.RUNTIME)  //运行时保留，可通过反射读取

//@Target：注解可以用在哪些元素上
@Target(ElementType.TYPE)             //只能用在类/接口上
@Target(ElementType.METHOD)          //只能用在方法上
@Target({ElementType.TYPE, ElementType.METHOD})  //可以用在多个位置
@Target(ElementType.TYPE_PARAMETER)  //泛型参数（JDK 8+）
@Target(ElementType.TYPE_USE)        //任意位置（JDK 8+）

//@Documented：注解包含在 Javadoc 中
@Documented
public @interface MyAnnotation { }

//@Inherited：子类是否继承父类的注解（JDK 8+）
@Inherited
public @interface MyAnnotation { }

//@Repeatable：注解可以重复使用（JDK 8+）
@Repeatable(Schedules.class)
public @interface Schedule {
    String dayOfWeek();
}

public @interface Schedules {
    Schedule[] value();
}
```

---

## 6.3 自定义注解

### 基本语法

```java
//@interface 定义注解
public @interface MyAnnotation {
    //注解属性（类似抽象方法）
    String value();        //必须设置值
    int count() default 1;  //有默认值，使用时可省略
}
```

### 使用注解

```java
//value 是唯一属性时，可以省略属性名
@MyAnnotation(value = "hello", count = 5)
public class MyClass { }

//如果只有一个 value 属性，可以简写
@MyAnnotation("hello")
public class MyClass { }

//使用有默认值的属性
@MyAnnotation(value = "test")
public class MyClass { }
```

### 带多种类型的属性

```java
public @interface Info {
    String name();              //字符串
    int age() default 18;       //整数，默认值
    String[] hobbies();         //数组
    Color color();              //枚举
    Class<?> clazz();           //Class 类型
}

@Info(name = "张三",
      age = 25,
      hobbies = {"读书", "编程"},
      color = Color.BLUE,
      clazz = String.class)
public class User { }

public enum Color {
    RED, GREEN, BLUE
}
```

---

## 6.4 反射概述

### 什么是反射

反射：在**运行时**动态获取类的结构信息（属性、方法、构造器等），并动态调用对象方法/访问字段的能力。

正常情况下，代码编译时就确定了要操作的类是哪个。反射让我们在运行时才知道要操作哪个类，灵活性大大增加。

### 反射的典型应用场景

- 框架（Spring、MyBatis）通过反射创建对象、调用方法
- JUnit 通过反射调用标注了 `@Test` 的方法
- JSON 序列化库通过反射读取字段进行转换
- 动态代理基于反射实现

---

## 6.5 Class 类

### Class 对象

每个类被加载后，JVM 会生成一个 `Class` 类型的对象，这个对象包含了类的完整结构信息。

```java
//获取 Class 对象的 4 种方式
Class<?> clazz1 = String.class;              //方式1：类名.class
Class<?> clazz2 = new String().getClass();   //方式2：对象.getClass()
Class<?> clazz3 = Class.forName("java.lang.String");  //方式3：Class.forName()
Class<?> clazz4 = ClassLoader.getSystemClassLoader().loadClass("java.lang.String");
```

### Class 常用方法

```java
Class<?> clazz = User.class;

//获取基本信息
clazz.getName();           //完整类名：com.example.User
clazz.getSimpleName();     //简单类名：User
clazz.getPackage();        //包信息
clazz.getSuperclass();     //父类
clazz.getInterfaces();     //实现的接口数组
clazz.getModifiers();      //访问修饰符

//判断类型
clazz.isInterface();       //是否是接口
clazz.isArray();           //是否是数组
clazz.isEnum();            //是否是枚举
clazz.isPrimitive();       //是否是基本类型
clazz.isAnnotation();      //是否是注解
clazz.isAnonymousClass(); //是否是匿名类
clazz.isMemberClass();     //是否是成员内部类
clazz.isLocalClass();      //是否是局部类

//创建实例
Object obj = clazz.newInstance();  //调用无参构造（已过时）
Constructor<?> c = clazz.getConstructor();  //获取 public 无参构造
Object obj = c.newInstance();
```

---

## 6.6 反射操作构造器

### 获取构造器

```java
Class<?> clazz = User.class;

//获取所有 public 构造器
Constructor<?>[] constructors = clazz.getConstructors();

//获取指定构造器
Constructor<?> c1 = clazz.getConstructor();  //public 无参
Constructor<?> c2 = clazz.getConstructor(String.class, int.class);  //public 有参

//获取所有构造器（包括 private）
Constructor<?>[] allConstructors = clazz.getDeclaredConstructors();
Constructor<?> c3 = clazz.getDeclaredConstructor(String.class);  //private 构造器
```

### 调用构造器创建实例

```java
//调用 public 构造器
Constructor<?> c = clazz.getConstructor(String.class, int.class);
User user = (User) c.newInstance("张三", 25);

//暴力访问 private 构造器
Constructor<?> cPrivate = clazz.getDeclaredConstructor(String.class);
cPrivate.setAccessible(true);  //取消访问检查
User user2 = (User) cPrivate.newInstance("李四");
```

---

## 6.7 反射操作字段

### 获取字段

```java
Class<?> clazz = User.class;

//获取所有 public 字段（包括父类）
Field[] fields = clazz.getFields();

//获取所有字段（包括 private，不包括父类）
Field[] allFields = clazz.getDeclaredFields();

//获取指定字段
Field nameField = clazz.getField("name");        //public
Field idField = clazz.getDeclaredField("id");    //private
```

### 读取/修改字段值

```java
User user = new User("张三", 25);
Class<?> clazz = user.getClass();

//读取 public 字段
Field nameField = clazz.getField("name");
Object value = nameField.get(user);  //获取 user 的 name 值

//修改 public 字段
nameField.set(user, "李四");  //修改 user 的 name 为"李四"

//读取/修改 private 字段
Field idField = clazz.getDeclaredField("id");
idField.setAccessible(true);  //取消访问检查
Object idValue = idField.get(user);  //读取 private 字段
idField.set(user, 10086);  //修改 private 字段
```

### 常用 Field 方法

```java
Field field = clazz.getDeclaredField("name");

field.getName();           //字段名
field.getType();           //字段类型
field.getModifiers();      //修饰符（public/private/static 等）
field.get(user);           //获取值
field.set(user, "value");  //设置值
field.setAccessible(true); //暴力访问
```

---

## 6.8 反射操作方法

### 获取方法

```java
Class<?> clazz = User.class;

//获取所有 public 方法（包括父类 Object）
Method[] methods = clazz.getMethods();

//获取所有方法（包括 private，不包括父类）
Method[] allMethods = clazz.getDeclaredMethods();

//获取指定方法（方法名 + 参数类型）
Method m1 = clazz.getMethod("toString");  //public
Method m2 = clazz.getDeclaredMethod("setName", String.class);  //private
```

### 调用方法

```java
User user = new User("张三", 25);
Class<?> clazz = user.getClass();

//调用 public 方法
Method setAge = clazz.getMethod("setAge", int.class);
setAge.invoke(user, 30);  //等同于 user.setAge(30)

//调用 private 方法
Method getId = clazz.getDeclaredMethod("getId");
getId.setAccessible(true);
Object id = getId.invoke(user);  //调用 user.getId()

//调用静态方法（对象参数传 null）
Method staticMethod = clazz.getDeclaredMethod("staticMethod");
staticMethod.invoke(null);
```

### 反射调用 vs 正常调用

```java
//正常调用
user.setAge(30);
user.getName();

//反射调用
Method setAge = clazz.getMethod("setAge", int.class);
setAge.invoke(user, 30);

Method getName = clazz.getMethod("getName");
Object name = getName.invoke(user);
```

### 常用 Method 方法

```java
Method method = clazz.getDeclaredMethod("setName", String.class);

method.getName();           //方法名
method.getReturnType();      //返回类型
method.getParameterTypes();  //参数类型数组
method.getExceptionTypes();  //异常类型数组
method.getModifiers();       //修饰符
method.invoke(obj, args);   //调用方法
method.setAccessible(true);  //暴力访问
```

---

## 6.9 反射操作泛型

### 获取泛型信息

```java
//泛型类型在编译后被擦除，但可以通过反射获取
public class UserDao extends Dao<User, Long> {
    public User findById(Long id) { return null; }
}

Class<?> clazz = UserDao.class;

//获取父类的泛型类型
Type type = clazz.getGenericSuperclass();
ParameterizedType paramType = (ParameterizedType) type;
Type[] typeArgs = paramType.getActualTypeArguments();
Class<?> entityClass = (Class<?>) typeArgs[0];  //User
Class<?> idClass = (Class<?>) typeArgs[1];     //Long

//获取字段的泛型类型
Field field = clazz.getDeclaredField("name");  //假设 name 是 String 类型
Class<?> fieldType = field.getType();  //String
```

---

## 6.10 动态代理

### 概念

动态代理：在运行时动态创建一个代理对象，代替真实对象，控制对它的访问。

- **静态代理**：编译时就知道要代理哪个类，代码写死
- **动态代理**：运行时才知道代理谁，更灵活

### JDK 动态代理

必须基于接口，代理类在运行时自动生成：

```java
//接口
public interface UserService {
    void addUser(String name);
    void deleteUser(Long id);
}

//真实对象
public class UserServiceImpl implements UserService {
    @Override
    public void addUser(String name) {
        System.out.println("添加用户: " + name);
    }
    
    @Override
    public void deleteUser(Long id) {
        System.out.println("删除用户: " + id);
    }
}

//InvocationHandler：代理逻辑
public class MyInvocationHandler implements InvocationHandler {
    private Object target;  //真实对象
    
    public MyInvocationHandler(Object target) {
        this.target = target;
    }
    
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        System.out.println("方法执行前...");
        Object result = method.invoke(target, args);  //调用真实对象方法
        System.out.println("方法执行后...");
        return result;
    }
}

//创建代理对象
UserService realService = new UserServiceImpl();
UserService proxyService = (UserService) Proxy.newProxyInstance(
    realService.getClass().getClassLoader(),  //类加载器
    realService.getClass().getInterfaces(),   //接口
    new MyInvocationHandler(realService)     //代理逻辑
);

proxyService.addUser("张三");  //通过代理调用
```

### CGLIB 动态代理

基于继承，不要求接口，性能更好（Spring 大量使用）：

```java
import net.sf.cglib.proxy.Enhancer;
import net.sf.cglib.proxy.MethodInterceptor;
import net.sf.cglib.proxy.MethodProxy;

public class CglibInterceptor implements MethodInterceptor {
    private Object target;
    
    public CglibInterceptor(Object target) {
        this.target = target;
    }
    
    @Override
    public Object intercept(Object o, Method method, Object[] args, MethodProxy proxy) throws Throwable {
        System.out.println("方法执行前...");
        Object result = proxy.invokeSuper(o, args);  //调用父类方法
        System.out.println("方法执行后...");
        return result;
    }
}

//创建代理（不需要接口）
Enhancer enhancer = new Enhancer();
enhancer.setSuperclass(UserServiceImpl.class);  //设置父类
enhancer.setCallback(new CglibInterceptor(new UserServiceImpl()));
UserServiceImpl proxy = (UserServiceImpl) enhancer.create();

proxy.addUser("张三");
```

### JDK 代理 vs CGLIB

| 区别 | JDK 动态代理 | CGLIB 动态代理 |
|------|-------------|---------------|
| 实现方式 | 基于接口 | 基于继承 |
| 代理类生成 | 运行时生成 `.class` | 运行时生成字节码 |
| 性能 | 稍慢 | 更快 |
| 限制 | 必须有接口 | 不能代理 final 类/final 方法 |
| 典型应用 | RMI、Spring 默认代理 | Spring、Hibernate |

---

## 6.11 反射与注解结合

### 简易 ORM 框架实现

```java
//表注解
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Table {
    String value();
}

//字段注解
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface Column {
    String name();
}

//实体类
@Table("t_user")
public class User {
    @Column("id")
    private Long id;
    
    @Column("user_name")
    private String name;
    
    @Column("age")
    private Integer age;
}

//通用保存方法
public void save(Object entity) throws Exception {
    Class<?> clazz = entity.getClass();
    
    //获取表名
    Table table = clazz.getAnnotation(Table.class);
    String tableName = table.value();
    
    //拼接 SQL
    StringBuilder sql = new StringBuilder("INSERT INTO " + tableName + " (");
    Field[] fields = clazz.getDeclaredFields();
    
    List<Object> values = new ArrayList<>();
    for (Field field : fields) {
        Column col = field.getAnnotation(Column.class);
        if (col != null) {
            sql.append(col.name()).append(", ");
            field.setAccessible(true);
            values.add(field.get(entity));
        }
    }
    sql.setLength(sql.length() - 2);
    sql.append(") VALUES (");
    for (int i = 0; i < values.size(); i++) {
        sql.append("?, ");
    }
    sql.setLength(sql.length() - 2);
    sql.append(")");
    
    System.out.println("SQL: " + sql);
    System.out.println("Values: " + values);
}

User user = new User();
user.setId(1L);
user.setName("张三");
user.setAge(25);
save(user);
//输出: INSERT INTO t_user (id, user_name, age) VALUES (?, ?, ?)
```

---

## 6.12 反射性能

### 反射的性能问题

- 每次调用都要经过安全检查（`setAccessible` 可以跳过）
- 方法调用需要字符串查找
- 无法JIT优化

### 优化方式

```java
//1. setAccessible(true) 跳过安全检查
Method method = clazz.getDeclaredMethod("method");
method.setAccessible(true);  //性能提升显著

//2. 缓存 Method/Constructor 对象
//不要每次反射都重新获取
Map<String, Method> methodCache = new ConcurrentHashMap<>();

//3. 使用反射基准测试
//如果性能要求极高，考虑：
//- MethodHandle（JDK 7+，更低层）
//- 字节码生成（ASM、Javassist）
```

---

## 6.13 常见面试题

### Q1：@Override 注解的作用？

标记方法是对父类方法的重写，编译器会检查该方法是否真的存在于父类中，如果不存在则报错，防止拼写错误。

### Q2：反射为什么慢？

每次反射调用都要经过访问检查、方法名查找、参数处理，性能低于直接调用。`setAccessible(true)` 可以部分优化。

### Q3：如何破坏单例？

通过反射调用私有构造器：

```java
Class<?> clazz = Singleton.class;
Constructor<?> c = clazz.getDeclaredConstructor();
c.setAccessible(true);
Singleton s1 = (Singleton) c.newInstance();
Singleton s2 = (Singleton) c.newInstance();
//s1 != s2，单例被破坏
```

防范方式：在构造方法中检查实例是否已存在：

```java
private Singleton() {
    if (instance != null) {
        throw new RuntimeException("单例不允许重复创建");
    }
}
```

---

## 📌 本章小结

Ch06 覆盖了 Java 注解与反射核心知识点：

- **内置注解**：@Override、@Deprecated、@SuppressWarnings、@FunctionalInterface
- **元注解**：@Retention、@Target、@Documented、@Inherited、@Repeatable
- **自定义注解**：@interface 定义、注解属性、默认值
- **Class 对象**：获取类信息、创建实例
- **反射操作**：构造器、字段、方法的获取与调用
- **动态代理**：JDK 代理（基于接口）、CGLIB（基于继承）
- **注解应用**：与反射结合实现 ORM 等框架功能

下一章：**Ch07 - Java I/O 流**，输入输出操作。
