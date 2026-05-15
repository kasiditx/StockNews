# Stock Telegram Alert

เครื่องมือแจ้งเตือนหุ้นผ่าน Telegram โดยดึงราคาจาก Yahoo Finance, วิเคราะห์กราฟด้วย technical indicators พื้นฐาน และดึงข่าวล่าสุดของแต่ละ ticker เพื่อช่วยให้เห็นหุ้นที่ควรจับตามองเร็วขึ้น

> ข้อมูลนี้เป็นเครื่องมือช่วยติดตาม ไม่ใช่คำแนะนำการลงทุน ต้องตรวจสอบข่าว งบการเงิน ความเสี่ยง และแผนลงทุนของตัวเองก่อนตัดสินใจเสมอ

## สิ่งที่ระบบทำ

- ดึงราคาย้อนหลังของหุ้นใน watchlist
- วิเคราะห์แนวโน้มด้วย SMA, RSI, MACD, volume และ breakout
- ดึงข่าวล่าสุดต่อ ticker จาก Yahoo Finance RSS
- สรุปว่าแต่ละบริษัททำธุรกิจอะไรจากไฟล์ config ที่ผู้ใช้กำหนดเอง
- ให้คะแนน signal แบบโปร่งใส พร้อมเหตุผลว่าทำไมควรจับตา
- ส่ง Telegram เป็น digest จัดอันดับเฉพาะตัวที่ score ถึง threshold
- ลดโอกาสโดน news rate limit โดยวิเคราะห์กราฟและจัดอันดับก่อน แล้วค่อยดึงข่าวเฉพาะหุ้น top list

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

## ใช้รายชื่อหุ้นจำนวนมาก

ไม่ควรใส่หุ้นทุกตัวลง `STOCK_WATCHLIST=` โดยตรง เพราะ env var จะยาวมาก ดูแลยาก และอาจทำให้ระบบยิง request หลายพันตัวในรอบเดียว

ถ้าต้องการสแกน universe กว้าง ๆ ให้ใช้:

```bash
STOCK_WATCHLIST=ALL
STOCK_UNIVERSE=US,TH
MAX_SYMBOLS_PER_RUN=300
TOP_ALERTS_PER_RUN=0
```

รายละเอียด:

- `US` ดึงรายชื่อหุ้นจาก Nasdaq Trader symbol directory และกรอง ETF/test issue ออก
- `TH` โหลดจากไฟล์ `config/universe.th.csv` โดยต้องมี columns `ticker,name,business`
- ใช้ `config/universe.th.example.csv` เป็นตัวอย่าง แล้วสร้าง `config/universe.th.csv` สำหรับรายชื่อจริง
- `MAX_SYMBOLS_PER_RUN` เป็น safety cap กัน runtime ยาวและ provider rate limit ถ้าตั้ง `0` คือไม่จำกัด
- `TOP_ALERTS_PER_RUN=0` ส่งทุกตัวที่เข้าเกณฑ์ ถ้าใส่เลขมากกว่า 0 จะจำกัดจำนวนต่อรอบ
- ระบบแบ่ง Telegram digest เป็นชุดละ 10 ตัว เพื่อไม่ให้ข้อความยาวเกิน
- ข่าวจะถูกดึงเฉพาะหุ้นที่ผ่าน ranking แล้ว ไม่ดึงข่าวทุกตัวใน universe

ตัวอย่างไฟล์ `config/universe.th.csv`:

```csv
ticker,name,business
PTT,PTT,Energy and petroleum business
AOT,Airports of Thailand,Airport operator
ADVANC,Advanced Info Service,Telecommunications
```

ระบบจะเติม `.BK` ให้อัตโนมัติสำหรับ ticker ไทยที่ยังไม่มี suffix

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
- ระบบจะไม่ฟันธงว่า “ขึ้นแน่” หรือ “กำไร 100-200%” แต่จะช่วยจัดอันดับ candidate ที่ควรศึกษาต่อจากราคา, momentum, volume และข่าว
