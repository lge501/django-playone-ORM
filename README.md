# Django練習
一個讓打排球的朋友找球打的網站<br>
租了場地有缺人可以上來徵臨打<br>
或是組織球團方便統整人數<br>
不必在FB社團每則留言確認的方式報名<br>

>測試使用<br>
帳號：t01@<span></span>gmail.com<br>
密碼：t01t01<br>
t01~t08都可用<br>

---
**用到的一些重點**
- [x] 用django-allauth接Facebook登入
- [x] 用繼承AbstractUser的自訂user model
- [x] 用select_related和prefetch_related減少觸及資料庫的次數
- [x] 能用generic view就用
- [x] 中英文國際化
- [x] player與group的多對多用中間model (membership) 額外存成員階級資訊
- [ ] 倒入各地球場地理資料，做縣市搜尋
- [ ] 用cache應付大量即時搜尋

---
