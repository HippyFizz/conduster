# Collectorjs

Это js код нашего пикселя который компилируется и минифицируется в ../collector/static/js/collector/conduster.js

### Установка
```
npm install
```

### Использование
1. Запускаем ```npm run watch```
1. Пишем код в ./conduster.js
1. watcher будет билдить итоговый файл в ../collector/static/js/collector/conduster.js
1. Не забываем этот файл по окончании работы коммитить в гит!!!!

Если нужно сбилдить не минифицированный файл, то запускаем ```npm run watch-dev```

Если нужно разово сбилдить, то запускаем ```npm run build```
