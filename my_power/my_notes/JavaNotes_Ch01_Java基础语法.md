# Ch01 - Java 基础语法

## 1.1 Java 程序结构

Java 程序最基本的结构：

```java
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
```

- `public class` 类名必须与文件名一致，一个 `.java` 文件只能有一个 `public class`
- `main` 方法是程序入口，格式固定：`public static void main(String[] args)`
- `{}` 成对出现，表示代码块作用域

---

## 1.2 数据类型

Java 是强类型语言，分为两大类：

### 基本数据类型（8种）

| 类型 | 占用字节 | 取值范围 | 默认值 |
|------|---------|---------|-------|
| byte | 1 | -128 ~ 127 | 0 |
| short | 2 | -32768 ~ 32767 | 0 |
| int | 4 | -2³¹ ~ 2³¹-1 | 0 |
| long | 8 | -2⁶³ ~ 2⁶³-1 | 0L |
| float | 4 | IEEE 754 单精度 | 0.0f |
| double | 8 | IEEE 754 双精度 | 0.0d |
| char | 2 | Unicode 0 ~ 65535 | '\u0000' |
| boolean | 1 | true / false | false |

**注意：**
- 整数默认 `int`，浮点数默认 `double`
- long 型常量要加 `L`，float 型常量要加 `f` 或 `F`
- `boolean` 不能用 0/1 替代，只能用 `true`/`false`

### 引用数据类型

- 类（Class）
- 接口（Interface）
- 数组（Array）
- 字符串（String）
- 默认值都是 `null`

---

## 1.3 变量与常量

### 变量

```java
int age = 25;              //局部变量，必须先赋值再使用
static int count = 0;      //静态变量，属于类
```

### 常量

```java
final double PI = 3.14159;   //final 修饰符，定义常量
//一旦赋值不能修改，命名全大写
```

### 类型转换

```java
//自动转换（隐式）：容量小 → 容量大
int a = 100;
long b = a;        //int 自动转 long

//强制转换（显式）：容量大 → 容量小
double d = 3.99;
int i = (int) d;   //结果为 3，小数部分丢失
```

---

## 1.4 运算符

### 算术运算符

`+ - * / %`（加减乘除取模）

```java
int a = 10, b = 3;
System.out.println(a / b);   //3（整数除法）
System.out.println(a % b);   //1（余数）
```

### 关系运算符

`== != > < >= <=`，返回 boolean

### 逻辑运算符

| 运算符 | 说明 | 特点 |
|-------|------|------|
| && | 逻辑与 | 短路：如果左边false，右边不执行 |
| \|\| | 逻辑或 | 短路：如果左边true，右边不执行 |
| ! | 逻辑非 | 取反 |

```java
int x = 5;
//&& 短路：i < 10 为 false，直接跳过后面的 ++x
boolean result = (x > 10) && (++x < 20);
//x 仍然是 5，因为 ++x 没执行
```

### 位运算符

`& | ^ ~ << >> >>>`（按位与、按位或、按位异或、按位取反、左移、右移、无符号右移）

```java
//左移：相当于 *2，左边溢出丢弃，右边补0
System.out.println(3 << 2);  //12 = 3 * 4
//右移：相当于 /2（带符号）
System.out.println(8 >> 1);  //4
```

### 三元运算符

```java
int max = (a > b) ? a : b;
//条件 ? 值1 : 值2
//条件为true取值1，否则取值2
```

---

## 1.5 控制流程

### 条件语句

```java
if (score >= 90) {
    grade = 'A';
} else if (score >= 80) {
    grade = 'B';
} else {
    grade = 'C';
}

//switch 支持：byte, short, int, char, String, enum
switch (day) {
    case 1:
        System.out.println("周一");
        break;
    case 2:
        System.out.println("周二");
        break;
    default:
        System.out.println("其他");
}
```

### 循环语句

**for 循环**（适合已知循环次数）

```java
for (int i = 0; i < 5; i++) {
    System.out.println(i);
}

//增强 for 循环（遍历数组/集合）
int[] arr = {1, 2, 3};
for (int num : arr) {
    System.out.println(num);
}
```

**while 循环**（适合不知道循环次数）

```java
while (condition) {
    //循环体
}
```

**do-while**（至少执行一次）

```java
do {
    //先执行一次
} while (condition);
```

### 跳转语句

- `break`：跳出当前循环
- `continue`：跳过本次循环，进入下次循环
- `return`：跳出整个方法

---

## 1.6 数组

### 声明与初始化

```java
//静态初始化
int[] arr1 = {1, 2, 3};
int arr2[] = new int[]{1, 2, 3};

//动态初始化
int[] arr3 = new int[5];  //默认0填充，长度固定5

//二维数组
int[][] matrix = {
    {1, 2, 3},
    {4, 5, 6}
};
```

### 数组操作常用方法

```java
int[] arr = {3, 1, 2};
Arrays.sort(arr);         //排序：[1, 2, 3]
int len = arr.length;      //长度：3
Arrays.toString(arr);     //转字符串
```

### 数组拷贝

```java
int[] original = {1, 2, 3};
int[] copy = Arrays.copyOf(original, original.length);
int[] copyPart = Arrays.copyOfRange(original, 1, 3); //[2, 3]
```

---

## 1.7 方法（函数）

### 基本结构

```java
访问修饰符 返回类型 方法名(参数类型 参数名) {
    //方法体
    return 结果;
}
```

### 示例

```java
public static int add(int a, int b) {
    return a + b;
}

//可变参数（参数数量可变）
public static int sum(int... nums) {
    int total = 0;
    for (int num : nums) {
        total += num;
    }
    return total;
}
sum(1, 2, 3);  //调用可变参数方法
```

### 方法重载（Overload）

- 同一个类中
- 方法名相同
- 参数列表不同（个数、类型、顺序）
- 与返回值无关

```java
int add(int a, int b) { return a + b; }
double add(double a, double b) { return a + b; }  //重载
int add(int a, int b, int c) { return a + b + c; } //重载
```

---

## 1.8 常用类库

### String

```java
String s = "Hello";
s.length();              //长度
s.charAt(0);             //取字符 'H'
s.substring(1, 3);       //截取 "el"
s.indexOf("ll");         //查找位置
s.toLowerCase();         //转小写
s.toUpperCase();         //转大写
s.trim();                //去首尾空格
s.split(",");            //分割
s.replace("l", "L");     //替换
s.contains("el");        //是否包含
s.isEmpty();             //是否为空字符串
```

**StringBuilder（可变字符串，线程不安全，效率高）**

```java
StringBuilder sb = new StringBuilder();
sb.append("Hello");
sb.append(" World");
sb.toString();  //"Hello World"
```

**StringBuffer（线程安全，同步开销大）**

```java
StringBuffer sb = new StringBuffer();
//用法同 StringBuilder，但线程安全
```

### Arrays

```java
int[] arr = {3, 1, 2};
Arrays.sort(arr);
Arrays.binarySearch(arr, 2);   //二分查找，返回索引
Arrays.copyOf(arr, 10);        //扩容拷贝
Arrays.fill(arr, 0);           //填充
Arrays.equals(arr1, arr2);     //比较
```

### Math

```java
Math.max(1, 3);       //3
Math.min(1, 3);       //1
Math.abs(-5);         //5
Math.pow(2, 3);       //8.0
Math.sqrt(9);         //3.0
Math.random();        //[0,1) 随机数
Math.round(3.7);      //4 四舍五入
```

### Object

```java
Object obj = new Object();
obj.toString();           //返回类名@哈希码
obj.equals(obj2);        //比较地址
obj.hashCode();          //哈希码
obj.getClass();          //获取Class对象
```

---

## 1.9 键盘输入

```java
import java.util.Scanner;

Scanner scanner = new Scanner(System.in);

int age = scanner.nextInt();       //读取整数
String name = scanner.nextLine();  //读取一行
double score = scanner.nextDouble();//读取小数
boolean flag = scanner.nextBoolean();//读取布尔

scanner.close();  //用完关闭
```

---

## 1.10 包的创建与使用

### 命名规范

- 全小写：com.company.project
- 避免关键字冲突
- 禁止数字开头

### 常用包

| 包 | 说明 |
|---|---|
| java.lang | 核心类（String, Object, System等），自动导入 |
| java.util | 工具类（集合、Scanner等） |
| java.io | 输入输出流 |
| java.net | 网络编程 |
| java.time | 日期时间（JDK 8+） |

### import 导包

```java
import java.util.ArrayList;     //精确导入
import java.util.*;             //通配符导入
import static java.lang.Math.PI;//静态导入
```

---

## 📌 本章小结

Ch01 覆盖了 Java 最基础的语法要素：数据类型、变量常量、运算符、控制流程、数组、方法、常用类库和输入输出。

下一章：**Ch02 - 面向对象三大特性**（封装、继承、多态），这是 Java 最核心的部分。
