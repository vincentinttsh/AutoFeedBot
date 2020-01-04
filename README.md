# 自動餵食器

## 動機

1. 遠程也能照顧毛小孩
    - 出門在外也能遠端遙控
2. 控制定時定量
    - 透過schedule功能排定餵食行程
3. 化簡餵食步驟
    - 讓餵食可以簡化到一鍵控制，只需人工填補飼料與清洗飼料盆

## 需求模型

1.可拆式飼料儲存罐
2.中控盒
3.飼料碗
4.遙控器(Telegram bot)
![](https://i.imgur.com/aiA1bD1.png)


## 主要功能
![](https://i.imgur.com/9qEnx2c.png)
- `/start`
    - 啟動telegram bot
    ![](https://i.imgur.com/D74k9AX.png)

- `/help`
    - 查詢指令說明
![](https://i.imgur.com/vTYAXHQ.png)

- `/feed`
    - 即刻餵食
![](https://i.imgur.com/PQqGOfZ.png)

- `/schedule`
    - 每日餵食排程
    ![](https://i.imgur.com/eMr537z.png)




## 素材

|材料|數量|用途|來源(金額)|
|---|---|---|---|
|紙箱|1|控制箱|MOLi (網購好夥伴)|
|紙板|n|零件 ex:擋板、梯子|MOLi (網購好夥伴)|
|寶特瓶|2|漏斗、飼料罐|MOLi (每日糖分攝取成就)|
|吸管|1|轉軸|moly|
|伺服馬達|1|控制擋板開啟角度|USR計畫零件($60)|
|raspberry pi|1|控制面板|MOLi ($1750)|

![](https://i.imgur.com/cwBnG92.jpg)

## DIY流程
![](https://i.imgur.com/OK7Gkxz.png)

![](https://i.imgur.com/Qqksdf1.png)

![](https://i.imgur.com/HhTOvBU.png)

![](https://i.imgur.com/om8uOn8.png)

![](https://i.imgur.com/gcL2EWb.png)

![](https://i.imgur.com/QJWqXv3.png)

![](https://i.imgur.com/7B5p7p1.png)







## 安裝

1. `sudo apt install python3-pip ` : 安裝
2. 安裝套件（兩者則一）
    1. `sudo pip3 install -r requirements.txt`
    2. `sudo pip3 install pipenv` + `pipenv sync`
3. 創建紀錄telegram bot token的檔案:
    ```
    echo "[TELEGRAM] 
    ACCESS_TOKEN = <token>" >> config.ini
    ```
5. 啟動( 如使用 pipenv ，請先下`pipenv shell` ) 
    1. `python3 main.py`

## 分工
107213004郭子緯 : `軟體功能撰寫` `口頭報告` `文件製作`

106213017蔡佳軒 : `裝置設計搜尋&組裝` `口頭報告` `文件製作`

105213018黃雅琳 : `點子發想` `裝置設計搜尋&組裝` `文件製作`


