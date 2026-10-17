name="Murshida"
age="20"
salary="2000.00"
is_active=True

print(name)
print(age)
print(salary)
print(is_active)

print(type(name))
print(type(age))
print(type(salary))
print(type(is_active))

fruits=["apple","banana"]
print(fruits)
print(len(fruits))
print(type(fruits))

print(fruits[0])
print(fruits[1])
print(fruits[1:3])
print(fruits[:3])
print(fruits[1:])

fruits[0]="orange"
print(fruits)

fruits[:2]="kiwi","Chikku"
print(fruits)

fruits.append(1)
print(fruits)

fruits.insert(0,0)
print(fruits)

veg=["tomato","potato"]
print(veg)

fruits.extend(veg)
print(fruits)

fruits.remove("potato")
print(fruits)

fruits.pop(1)
print(fruits)

fruits.pop()
print(fruits)

del fruits[0]
print(fruits)

veg=["tomato","potato","orange"]
print(veg)

veg.sort()
print(veg)

veg.sort(reverse=True)
print(veg)

food=fruits+veg
print(food)

food.clear()
print(food)

del food
print(food)

