# Ch02 - 面向对象三大特性

## 2.1 类与对象

### 定义类

```java
public class Student {
    //属性（字段）
    private String name;
    private int age;
    
    //构造方法
    public Student() {
    }
    
    public Student(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    //方法
    public void study() {
        System.out.println(name + "正在学习");
    }
    
    //getter/setter
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
}
```

### 创建对象

```java
Student s1 = new Student();           //调用无参构造
Student s2 = new Student("张三", 20);  //调用有参构造
```

### 内存分区

| 区域 | 存放内容 | 生命周期 |
|------|---------|---------|
| 栈（Stack） | 基本类型变量、引用变量（对象地址） | 方法结束即释放 |
| 堆（Heap） | new 创建的对象、数组 | 垃圾回收器决定 |
| 方法区 | 类信息、静态变量、字符串常量 | 整个程序运行期间 |

```java
Student s = new Student();
//s 在栈中，存的是堆中对象的地址
//new Student() 在堆中分配内存
```

---

## 2.2 封装

### 概念

封装：将属性私有化，提供公开的 getter/setter 访问通道，隐藏内部实现细节，对外提供受控的访问接口。

### 作用

1. 隐藏内部实现，保护数据安全
2. 统一入口，便于后期维护
3. 允许外部按预期方式访问

### 实现步骤

```java
public class User {
    //1. 属性私有化（禁止直接访问）
    private String username;
    private String password;
    private int age;
    
    //2. 公开 getter/setter（控制访问）
    public String getUsername() {
        return username;
    }
    
    public void setUsername(String username) {
        this.username = username;
    }
    
    //3. 可在 setter 中加校验
    public void setAge(int age) {
        if (age < 0 || age > 150) {
            throw new IllegalArgumentException("年龄不合法");
        }
        this.age = age;
    }
    
    public int getAge() {
        return age;
    }
}
```

### 访问修饰符

| 修饰符 | 同类 | 同包 | 子类 | 任意位置 |
|-------|------|------|------|---------|
| private | ✅ | ❌ | ❌ | ❌ |
| default（默认） | ✅ | ✅ | ❌ | ❌ |
| protected | ✅ | ✅ | ✅ | ❌ |
| public | ✅ | ✅ | ✅ | ✅ |

- `private`：最严格，类内部可见
- `public`：最开放，任意位置可见
- `protected`：子类和同包可见
- `default`：同包可见，不写修饰符默认为 default

### 封装原则

- **属性私有化**：`private` 修饰
- **方法公开化**：`public` 暴露必要操作
- **必要时加校验**：setter 中验证数据合法性
- **提供只读或只写**：按需决定是否暴露 setter/getter

---

## 2.3 继承

### 概念

继承：子类自动拥有父类的属性和方法，实现代码复用，子类可以在父类基础上进行扩展。

### 基本语法

```java
//extends 关键字实现继承
public class Animal {
    protected String name;
    protected int age;
    
    public void eat() {
        System.out.println("动物在吃东西");
    }
}

public class Dog extends Animal {
    //自动拥有 name, age 属性
    //自动拥有 eat() 方法
    
    private String color;  //子类独有属性
    
    public void bark() {
        System.out.println("狗在叫");
    }
}
```

### instanceof 和类型转换

```java
Animal a = new Dog();
if (a instanceof Dog) {
    Dog d = (Dog) a;  //向下转型
    d.bark();
}
```

### 继承的特点

1. **单继承**：Java 只支持单继承，一个类只能有一个直接父类
2. **多层继承**：可以形成继承链（A → B → C）
3. **所有类默认继承 Object**：`class A` 等同于 `class A extends Object`

### 方法重写（Override）

子类重新定义父类已有的方法，要求：
- 方法名、参数列表完全相同
- 返回类型可以是父类返回类型的子类型
- 访问权限不能比父类更严格
- 不能重写 `static`、`final`、`private` 方法

```java
public class Animal {
    public void sound() {
        System.out.println("动物叫");
    }
}

public class Cat extends Animal {
    @Override
    public void sound() {
        System.out.println("猫叫：喵喵喵");
    }
}
```

### super 关键字

`super` 代表父类引用，用于：
- 调用父类构造方法：`super(...)`
- 调用父类方法：`super.method()`
- 访问父类属性：`super.field`

```java
public class Dog extends Animal {
    private String color;
    
    public Dog(String name, int age, String color) {
        super(name, age);  //调用父类有参构造
        this.color = color;
    }
    
    public void sound() {
        super.sound();  //先调用父类方法
        System.out.println("汪汪汪");
    }
}
```

### 继承中的构造方法

规则：
- 子类构造时**必须先调用父类构造**
- 默认调用父类无参构造 `super()`
- 如果父类没有无参构造，子类**必须显式调用**父类有参构造

```java
public class Animal {
    private String name;
    
    public Animal(String name) {  //父类只有有参构造
        this.name = name;
    }
}

public class Dog extends Animal {
    private String color;
    
    public Dog(String name, String color) {
        super(name);  //必须显式调用
        this.color = color;
    }
}
```

### 继承的优缺点

**优点：** 代码复用，扩展方便，建立清晰的类层次结构

**缺点：** 高度耦合，父类变化影响子类；单继承限制复杂度

---

## 2.4 多态

### 概念

多态：同一类型的引用，指向不同对象时，表现出的不同行为形态。

### 实现前提

1. 继承关系存在
2. 子类重写父类方法
3. 父类引用指向子类对象（向上转型）

### 两种形式

#### 引用多态

```java
Animal a1 = new Dog();   //父类引用指向子类对象
Animal a2 = new Cat();   //同一类型，不同实现

a1.eat();  //调用 Dog 的 eat()
a2.eat();  //调用 Cat 的 eat()
```

#### 方法多态

```java
//方法重写：同一方法在不同子类中有不同实现
Animal a = new Dog();
a.eat();  //输出：狗在吃东西

a = new Cat();
a.eat();  //输出：猫在吃东西
```

### 向上转型与向下转型

```java
//向上转型（自动转换）：子类 → 父类
Animal a = new Dog();  //安全，总是可行

//向下转型（强制转换）：父类 → 子类
Animal a = new Dog();
Dog d = (Dog) a;       //安全，因为 a 实际就是 Dog

//不安全转型（编译通过，运行报错）
Animal a = new Cat();
Dog d = (Dog) a;       //ClassCastException
```

### instanceof 运行时类型检查

```java
if (a instanceof Dog) {
    Dog d = (Dog) a;  //转型前检查，避免 ClassCastException
}
```

### 多态的应用场景

**场景1：参数多态**

```java
public void feed(Animal a) {
    a.eat();
}

feed(new Dog());   //传入狗
feed(new Cat());   //传入猫
```

**场景2：返回多态**

```java
public Animal createAnimal(String type) {
    if ("dog".equals(type)) {
        return new Dog();
    } else {
        return new Cat();
    }
}
```

**场景3：集合多态**

```java
List<Animal> animals = new ArrayList<>();
animals.add(new Dog());
animals.add(new Cat());
for (Animal a : animals) {
    a.eat();  //多态调用
}
```

### 多态的优缺点

**优点：**
- 代码灵活，可扩展
- 降低类之间的耦合度
- 统一接口，屏蔽不同实现差异

**缺点：**
- 无法直接调用子类特有方法（需向下转型）
- 过多使用增加代码复杂度

---

## 2.5 抽象类与抽象方法

### 抽象方法

用 `abstract` 修饰，没有方法体的方法：

```java
public abstract void move();  //没有 {}，直接分号结束
```

### 抽象类

包含抽象方法的类必须声明为抽象类：

```java
public abstract class Animal {
    protected String name;
    
    //抽象方法：强制子类实现
    public abstract void move();
    
    //普通方法：子类可以直接继承
    public void sleep() {
        System.out.println("动物在睡觉");
    }
}
```

### 特点

1. **不能实例化**：`new Animal()` 错误
2. **可以有构造方法**：供子类 `super()` 调用
3. **子类必须重写所有抽象方法**，否则子类也必须是抽象类

```java
public class Dog extends Animal {
    @Override
    public void move() {
        System.out.println("狗在跑");
    }
}
```

---

## 2.6 接口

### 概念

接口是一种更纯粹的抽象类型，**只定义规范，不实现细节**。类通过 `implements` 来"承诺"遵守接口规范。

### 定义接口

```java
public interface Flyable {
    //接口中属性默认 public static final（常量）
    int MAX_SPEED = 1200;
    
    //接口中方法默认 public abstract（抽象方法）
    void fly();
    
    //JDK 8 开始支持 default 方法
    default void land() {
        System.out.println("降落");
    }
    
    //JDK 8 支持静态方法
    static void info() {
        System.out.println("飞行接口");
    }
}
```

### 实现接口

```java
public class Bird implements Flyable {
    @Override
    public void fly() {
        System.out.println("鸟儿在飞翔");
    }
}
```

### 接口特点

1. **不能实例化**：`new Flyable()` 错误
2. **接口属性默认 `public static final`**：常量
3. **接口方法默认 `public abstract`**：抽象方法
4. **支持多实现**：类可以同时实现多个接口

```java
public class Duck implements Flyable, Swimmable {
    @Override
    public void fly() { }
    
    @Override
    public void swim() { }
}
```

### 接口与抽象类的区别

| 区别 | 抽象类 | 接口 |
|------|-------|------|
| 关键字 | `abstract class` | `interface` |
| 继承/实现 | 单继承 | 多实现 |
| 属性 | 任意类型 | 默认常量 |
| 方法 | 抽象+非抽象 | 默认抽象+JDK8 default/static |
| 构造方法 | 有 | 无 |
| 适用场景 | 模板继承 is-a | 能力扩展 like-a |

---

## 2.7 内部类

### 成员内部类

```java
public class Outer {
    private int a = 10;
    
    public class Inner {
        public void show() {
            System.out.println(a);  //可以访问外部类属性
        }
    }
}

//创建内部类对象
Outer.Inner inner = new Outer().new Inner();
```

### 静态内部类

```java
public class Outer {
    static class Inner {
        public void show() {
            System.out.println("静态内部类");
        }
    }
}

//创建
Outer.Inner inner = new Outer.Inner();
```

### 局部内部类

```java
public void method() {
    class LocalInner {
        public void show() { }
    }
    LocalInner li = new LocalInner();
}
```

### 匿名内部类

没有名字的内部类，常用于**简化监听器/回调**：

```java
//传统写法
class MyListener implements OnClickListener {
    @Override
    public void onClick() { }
}
button.setOnClickListener(new MyListener());

//匿名内部类写法
button.setOnClickListener(new OnClickListener() {
    @Override
    public void onClick() {
        System.out.println("点击");
    }
});

//JDK 8+ lambda（接口只有一个方法时可用）
button.setOnClickListener(e -> System.out.println("点击"));
```

---

## 2.8 关键字总结

| 关键字 | 作用 |
|-------|------|
| this | 当前对象引用 |
| super | 父类引用 |
| static | 静态（类级别，优先于对象存在） |
| final | 修饰变量=常量，修饰方法=不能重写，修饰类=不能继承 |
| abstract | 修饰类=抽象类，修饰方法=抽象方法 |
| interface | 接口 |
| implements | 实现接口 |
| extends | 继承 |

### static 详解

```java
public class Counter {
    static int count = 0;  //所有对象共享
    
    public Counter() {
        count++;  //每次创建对象计数
    }
    
    static int getCount() {  //静态方法
        return count;  //只能访问静态成员
    }
}
```

### final 详解

```java
final int MAX = 100;       //常量，不能修改
final double PI = 3.14159;

final class Animal { }     //不能被继承
//public final class Dog extends Animal {}  //错误

final void show() { }      //不能被重写
//class Cat extends Animal { @Override void show() {} } //错误
```

---

## 📌 本章小结

Ch02 覆盖了面向对象三大特性核心知识点：

- **封装**：属性私有化 + 公开访问器，保护数据安全
- **继承**：`extends`，单继承，建立 is-a 关系
- **多态**：父类引用指向子类对象 + 方法重写，统一接口

以及抽象类、接口、内部类等扩展概念。

下一章：**Ch03 - 异常处理**，Java 程序的错误捕捉与处理机制。
