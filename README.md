# Stock Telegram Alert

เครื่องมือแจ้งเตือนหุ้นผ่าน Telegram โดยดึงราคาจาก Yahoo Finance, วิเคราะห์กราฟด้วย technical indicators พื้นฐาน และดึงข่าวล่าสุดของแต่ละ ticker เพื่อช่วยให้เห็นหุ้นที่ควรจับตามองเร็วขึ้น

> ข้อมูลนี้เป็นเครื่องมือช่วยติดตาม ไม่ใช่คำแนะนำการลงทุน ต้องตรวจสอบข่าว งบการเงิน ความเสี่ยง และแผนลงทุนของตัวเองก่อนตัดสินใจเสมอ

## สิ่งที่ระบบทำ

- ดึงราคาย้อนหลังของหุ้นใน watchlist
- วิเคราะห์แนวโน้มด้วย SMA, RSI, MACD, volume และ breakout
- ดึงข่าวล่าสุดต่อ ticker จาก Yahoo Finance RSS
- สรุปว่าแต่ละบริษัททำธุรกิจอะไรจากไฟล์ config ที่ผู้ใช้กำหนดเอง
- ให้คะแนน signal แบบโปร่งใส พร้อมเหตุผลว่าทำไมควรจับตา
- ส่ง Telegram เฉพาะตัวที่ score ถึง threshold

## ติดตั้ง

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
cp config/watchlist.example.json config/watchlist.json
```

แก้ `.env`:

```bash
TELEGRAM_BOT_TOKEN=ใส่ token จาก BotFather
TELEGRAM_CHAT_ID=ใส่ chat id ของคุณ
STOCK_WATCHLIST=PTT.BK,AOT.BK,NVDA
```

หรือใช้ `config/watchlist.json` เพื่อใส่ชื่อบริษัทและธุรกิจให้ละเอียดขึ้น

## รันทันทีหนึ่งรอบ

```bash
python -m stock_alerts run-once --watchlist config/watchlist.json
```

## รันแบบเฝ้าดูต่อเนื่อง

```bash
python -m stock_alerts watch --watchlist config/watchlist.json
```

## ตรวจคุณภาพ

```bash
ruff check .
pytest
```

## ข้อควรระวัง

- อย่า commit `.env` เพราะมี Telegram token
- ถ้าข่าวไม่ขึ้น อาจเป็นข้อจำกัดของ Yahoo Finance RSS หรือ ticker ไม่รองรับ
- Technical signal ไม่ได้ทำนายอนาคต เป็นเพียงตัวช่วยกรองหุ้นที่ควรตรวจต่อ
