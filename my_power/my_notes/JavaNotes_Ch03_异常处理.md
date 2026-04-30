# Ch03 - 异常处理

## 3.1 异常概述

### 什么是异常

程序在运行过程中发生的非正常事件，叫异常（Exception）。Java 通过异常机制来处理这些问题，让程序不至于崩溃，而是可以优雅地报告错误、清理资源。

### 异常与错误的区别

| 类型 | 说明 | 处理方式 |
|------|------|---------|
| Error（错误） | JVM 本身问题，OutOfMemoryError 等 | 程序无法处理，终止 |
| Exception（异常） | 程序逻辑或环境问题 | 可以捕获、处理 |

### 异常体系结构

```
Throwable（可抛出的）
├── Error（错误）
│   ├── OutOfMemoryError
│   ├── StackOverflowError
│   └── ...
└── Exception（异常）
    ├── IOException（受检异常）
    ├── SQLException（受检异常）
    ├── RuntimeException（非受检异常）
    │   ├── NullPointerException
    │   ├── ArrayIndexOutOfBoundsException
    │   ├── ClassCastException
    │   ├── ArithmeticException
    │   └── ...
    └── 其他异常
```

---

## 3.2 异常分类：受检 vs 非受检

### 受检异常（Checked Exception）

编译器强制要求处理的异常，继承自 `Exception` 但不包括 `RuntimeException`：

```java
//必须用 try-catch 或 throws 声明，否则编译报错
try {
    FileReader fr = new FileReader("a.txt");
} catch (FileNotFoundException e) {
    e.printStackTrace();
}
```

常见受检异常：
- `IOException` / `FileNotFoundException`
- `SQLException`
- `ClassNotFoundException`
- `NoSuchMethodException`

### 非受检异常（Unchecked Exception）

编译器不强制处理，继承自 `RuntimeException`：

```java
//可以不处理，运行时才报错
int[] arr = {1, 2, 3};
System.out.println(arr[10]);  //ArrayIndexOutOfBoundsException
```

常见非受检异常：
- `NullPointerException`
- `ArrayIndexOutOfBoundsException`
- `ClassCastException`
- `ArithmeticException`
- `IllegalArgumentException`
- `NumberFormatException`

---

## 3.3 异常处理：try-catch-finally

### 基本语法

```java
try {
    //可能抛出异常的代码
    int result = 10 / 0;  //ArithmeticException
} catch (Exception e) {
    //捕获并处理异常
    System.out.println("出错了：" + e.getMessage());
} finally {
    //无论是否异常，都执行的代码
    System.out.println("始终执行");
}
```

### 执行顺序

```
情况1：正常执行
try → finally

情况2：抛出异常被捕获
try → catch → finally

情况3：异常未被捕获
try → finally → 程序终止（异常向上抛）
```

### 多重 catch

按异常类型从具体到宽泛排序：

```java
try {
    //代码
} catch (FileNotFoundException e) {
    //处理文件不存在
} catch (IOException e) {
    //处理IO错误（IOException 是 FileNotFoundException 父类，要放后面）
} catch (Exception e) {
    //兜底处理
}
```

### finally 的特性

```java
try {
    return;
} finally {
    System.out.println("仍会执行");  //即使 try return，finally 也会执行
}
```

**finally 不执行的情况：**
- `System.exit()` 终止 JVM
- 守护线程被终止
- 抛出 OOM 导致 JVM 崩溃

---

## 3.4 throw 与 throws

### throw：抛出异常

在代码内部主动抛出异常对象：

```java
public void withdraw(double amount) {
    if (amount <= 0) {
        throw new IllegalArgumentException("取款金额必须为正数");
    }
    if (amount > balance) {
        throw new InsufficientBalanceException("余额不足");
    }
    balance -= amount;
}
```

### throws：声明异常

在方法签名上声明该方法可能抛出的异常：

```java
//声明可能抛出多个异常
public void readFile() throws FileNotFoundException, IOException {
    FileReader fr = new FileReader("a.txt");  //可能抛 FileNotFoundException
    fr.read();                               //可能抛 IOException
}

//throws 可声明父类，隐去具体异常
public void readFile() throws Exception { }  //可捕获任何 Exception

//RuntimeException 可以不声明
public void test() {
    throw new RuntimeException("运行时异常");  //不需要 throws
}
```

### 方法覆盖中的 throws

子类覆盖父类方法时：
- 可以不声明异常
- 可以声明抛出父类异常的子类
- 不能声明抛出父类没有声明的异常

```java
class Parent {
    public void run() throws IOException { }
}

class Child extends Parent {
    @Override
    public void run() throws FileNotFoundException { }  //OK，FileNotFoundException 是 IOException 子类
}
```

---

## 3.5 常见异常详解

### NullPointerException（空指针异常）

最常见的异常，调用 `null` 对象的方法或属性时触发：

```java
String str = null;
str.length();  //NullPointerException

//正确做法：先判空
if (str != null) {
    str.length();
}
```

### ArrayIndexOutOfBoundsException

访问数组越界时触发：

```java
int[] arr = {1, 2, 3};
arr[3] = 4;  //ArrayIndexOutOfBoundsException，索引从0开始

//正确做法：先检查长度
if (index >= 0 && index < arr.length) {
    arr[index] = value;
}
```

### ClassCastException

类型强制转换失败：

```java
Object obj = new String("hello");
Integer num = (Integer) obj;  //ClassCastException

//正确做法：先用 instanceof 检查
if (obj instanceof Integer) {
    Integer num = (Integer) obj;
}
```

### NumberFormatException

字符串转数字格式错误：

```java
int num = Integer.parseInt("abc");  //NumberFormatException

//正确做法：异常捕获或正则校验
try {
    int num = Integer.parseInt("123");
} catch (NumberFormatException e) {
    System.out.println("不是有效数字");
}
```

### ArithmeticException

算术运算错误：

```java
int result = 10 / 0;  //ArithmeticException，除数不能为0
```

---

## 3.6 自定义异常

### 步骤

1. 继承 `Exception`（受检）或 `RuntimeException`（非受检）
2. 提供构造方法

### 示例：余额不足异常

```java
//受检异常（需要调用方处理）
public class InsufficientBalanceException extends Exception {
    public InsufficientBalanceException() { }
    
    public InsufficientBalanceException(String message) {
        super(message);
    }
    
    public InsufficientBalanceException(String message, Throwable cause) {
        super(message, cause);
    }
}

//非受检异常（运行时才报错）
public class InvalidParameterException extends RuntimeException {
    public InvalidParameterException(String message) {
        super(message);
    }
}
```

### 使用自定义异常

```java
public void withdraw(double amount) throws InsufficientBalanceException {
    if (amount > balance) {
        throw new InsufficientBalanceException("余额不足，当前余额：" + balance);
    }
    balance -= amount;
}

//调用
try {
    account.withdraw(1000);
} catch (InsufficientBalanceException e) {
    System.out.println(e.getMessage());
}
```

### 异常选择原则

| 场景 | 选择 |
|------|------|
| 调用方能恢复，需要处理 | 受检异常 `extends Exception` |
| 调用方无法恢复，编程错误 | 非受检异常 `extends RuntimeException` |
| 第三方库通常用受检异常强制处理 | 按库的设计来 |

---

## 3.7 异常链

将原始异常封装进新异常，保留错误追踪信息：

```java
try {
    //调用服务层
    userService.saveUser(user);
} catch (SQLException e) {
    //业务异常包装原始异常
    throw new BusinessException("保存用户失败", e);
}
```

### 异常链方法

```java
//方式1：构造方法传入原始异常
throw new BusinessException("保存失败", originalException);

//方式2：initCause + throw
throw (BusinessException) new BusinessException("保存失败").initCause(originalException);

//获取原始异常
catch (BusinessException e) {
    Throwable cause = e.getCause();  //获取原始异常
    cause.printStackTrace();
}
```

---

## 3.8 异常最佳实践

### 应该做的事

```java
//1. 具体捕获，具体处理
try {
    readConfig();
} catch (FileNotFoundException e) {
    //文件不存在：使用默认配置
    loadDefaultConfig();
} catch (IOException e) {
    //IO错误：记录日志，重试
    logger.error("读取配置文件失败", e);
    retry();
}

//2. 释放资源用 try-with-resources
try (FileInputStream fis = new FileInputStream("a.txt");
     BufferedInputStream bis = new BufferedInputStream(fis)) {
    //自动关闭流，无论是否异常
} catch (IOException e) {
    e.printStackTrace();
}

//3. 记录日志后再抛出
try {
    doSomething();
} catch (Exception e) {
    logger.error("操作失败", e);
    throw e;  //重新抛出，让上层处理
}
```

### 不应该做的事

```java
//❌ 空的 catch 块
try {
    file.read();
} catch (IOException e) {
    //什么都不做，异常消失了
}

//❌ 直接捕获 Exception/Throwable（吞掉所有异常）
try {
    doSomething();
} catch (Throwable t) {
    //太宽泛，不知道具体什么错
}

//❌ 在 finally 中抛异常（会覆盖 try 中的异常）
try {
    int x = 10 / 0;
} finally {
    throw new RuntimeException("finally 中的异常");  //原始异常丢失
}

//❌ 用异常做流程控制
try {
    list.get(i);
} catch (IndexOutOfBoundsException e) {
    //不要用异常代替 if 判断
}
```

---

## 3.9 try-with-resources

JDK 7+ 简化资源关闭，自动调用 `close()`：

### 基本用法

```java
//实现 AutoCloseable 接口的资源才能使用
try (BufferedReader br = new BufferedReader(new FileReader("a.txt"));
     BufferedWriter bw = new BufferedWriter(new FileWriter("b.txt"))) {
    String line;
    while ((line = br.readLine()) != null) {
        bw.write(line);
    }
} //自动关闭，br 和 bw 都会调用 close()
```

### 自定义资源类

```java
public class DatabaseConnection implements AutoCloseable {
    public void query(String sql) {
        System.out.println("执行: " + sql);
    }
    
    @Override
    public void close() throws Exception {
        System.out.println("关闭数据库连接");
    }
}

//使用
try (DatabaseConnection db = new DatabaseConnection()) {
    db.query("SELECT * FROM users");
} //自动调用 close()
```

---

## 3.10 异常信息获取

```java
try {
    int[] arr = {1, 2};
    System.out.println(arr[10]);
} catch (ArrayIndexOutOfBoundsException e) {
    e.getMessage();        //简短描述：10
    e.getClass().getName(); //异常类型：java.lang.ArrayIndexOutOfBoundsException
    e.printStackTrace();   //打印堆栈信息（生产环境不要用）
    
    //获取更详细信息
    StringWriter sw = new StringWriter();
    e.printStackTrace(new PrintWriter(sw));
    String stackTrace = sw.toString();
}
```

---

## 📌 本章小结

Ch03 覆盖了 Java 异常处理核心知识点：

- **异常体系**：Error vs Exception，Checked vs Unchecked
- **处理机制**：try-catch-finally，throw vs throws
- **常见异常**：NPE、数组越界、类型转换、数字格式
- **自定义异常**：继承 Exception 或 RuntimeException
- **异常链**：保留原始异常信息
- **最佳实践**：具体捕获、资源释放、避免空 catch
- **try-with-resources**：JDK 7+ 自动关闭资源

下一章：**Ch04 - 集合框架**，Java 中最常用的数据结构（List/Set/Map）。
