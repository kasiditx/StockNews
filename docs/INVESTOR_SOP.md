# PERSONAL STOCK INVESTOR SOP
> **Confidential · Updated May 18, 2026 · สำหรับ Kasidit**
>
> เป้าหมาย: ใช้ AI + Telegram bot เป็นผู้ช่วยคัดกรองหุ้นที่น่าจับตามองที่สุด เพื่อให้ผู้ใช้ตัดสินใจลงทุนได้ทันข่าว ทันกราฟ และไม่พลาดหุ้นที่มี momentum ดี โดยยังยึดหลักความเสี่ยงก่อนกำไรเสมอ

---

## 0. บทบาทของระบบ

ระบบนี้ไม่ใช่คนกดซื้อขายแทน และไม่ใช่คำแนะนำการลงทุนแบบฟันธง

บทบาทที่ถูกต้องคือ:

- สแกนหุ้นจำนวนมากในกลุ่มที่ผู้ใช้สนใจ
- คัดเฉพาะ **10 ตัวที่น่าจับตามองที่สุดต่อรอบ**
- เรียงอันดับจากแรงที่สุดเป็น `#1` แล้วไล่ลงมา
- สรุปว่าหุ้นแต่ละตัวทำธุรกิจอะไร
- วิเคราะห์กราฟ, trend, momentum, risk flags
- สรุปข่าว และตีความว่าข่าวเป็นบวก/ลบต่อราคามากน้อยแค่ไหน
- บอกว่าธุรกิจนั้นจำเป็นต่ออะไร และมีภาพอนาคตอย่างไร
- ช่วยลด FOMO, ลดการไล่ราคา, และช่วยให้ผู้ใช้ตัดสินใจอย่างมีระบบ

คำตัดสินสุดท้ายยังเป็นของผู้ใช้เสมอ

---

## 1. Universe ที่ต้องโฟกัส

ค่า runtime หลักของ bot:

```bash
STOCK_WATCHLIST=ALL
STOCK_UNIVERSE=US
STOCK_GROUPS=FINCIAL,INDUS,SERVICE,TECH
TOP_ALERTS_PER_RUN=10
MIN_SCORE_TO_ALERT=4
MAX_NEWS_LOOKUPS_PER_RUN=20
```

### 1.1 FINCIAL - ธุรกิจการเงิน

ครอบคลุม:

- `BANK` ธนาคาร
- `FIN` เงินทุนและหลักทรัพย์
- `INSUR` ประกันภัยและประกันชีวิต
- Banking & Financial Services
- Investment & Asset Management
- Insurance
- Fintech & Payment Network

ตัวอย่างหุ้นที่ต้องรู้จัก:

- `JPM` - ธนาคารขนาดใหญ่และแกนหลักของระบบการเงินสหรัฐ
- `BAC` - ธนาคารรายย่อยขนาดใหญ่ มีฐานลูกค้ากว้าง
- `PNC` - ธนาคารใหญ่ที่เน้นการเติบโตและเงินปันผล
- `BRK-A`, `BRK-B` - Berkshire Hathaway โฮลดิ้ง/ประกัน/ลงทุน
- `BLK` - BlackRock บริษัทจัดการสินทรัพย์ระดับโลก
- `V`, `MA` - payment network ระดับโลก
- `XYZ` - Block, Inc. เดิมคือ Square / SQ

### 1.2 INDUS - สินค้าอุตสาหกรรม

ครอบคลุม:

- `AUTO` ยานยนต์
- `IMM` วัสดุอุตสาหกรรมและเครื่องจักร
- `PETRO` ปิโตรเคมีและเคมีภัณฑ์
- `STEEL` เหล็กและผลิตภัณฑ์โลหะ
- Aerospace & Defense
- Machinery & Industrial Equipment
- Logistics & Transportation

ตัวอย่างหุ้นที่ต้องรู้จัก:

- `BA` - Boeing, การบินและอวกาศ
- `LMT` - Lockheed Martin, defense
- `CAT` - Caterpillar, เครื่องจักรหนัก
- `DE` - Deere, เครื่องจักรเกษตร
- `UPS`, `FDX` - logistics และขนส่ง
- `SIEGY` - Siemens, วิศวกรรมและเทคโนโลยีอุตสาหกรรม

### 1.3 SERVICE - บริการ

ครอบคลุม:

- `COMM` พาณิชย์
- `HELTH` การแพทย์
- `MEDIA` สื่อและสิ่งพิมพ์
- `PROF` บริการเฉพาะกิจ
- `TRANS` ขนส่งและโลจิสติกส์
- Communication Services
- Consumer Services
- Financial Services
- Cloud / Platform / Marketplace services

ตัวอย่างหุ้นที่ต้องรู้จัก:

- `AMZN` - E-commerce, Cloud, Marketplace
- `MSFT` - Cloud, Software, AI productivity
- `GOOGL` - Search, Ads, YouTube, Cloud, AI
- `META` - Social platform, Ads, AI infrastructure
- `ABNB` - Travel platform
- `V`, `MA` - payment service infrastructure

### 1.4 TECH - เทคโนโลยี

ครอบคลุม:

- `ICT`
- AI
- Semiconductor
- Cloud
- Software
- Cybersecurity
- Communication Infrastructure
- Future Innovation เช่น EV, automation, data center

ตัวอย่างหุ้นที่ต้องรู้จัก:

- `NVDA` - AI GPU, data center, accelerator
- `MSFT` - Cloud, enterprise software, AI
- `ADVANC` - ICT/telecom ฝั่งไทย ถ้ามี universe ไทย
- กลุ่ม cybersecurity, software, semiconductor, AI infrastructure

---

## 2. หลักการคัดหุ้น Top 10

ทุก notification ต้องคัดจาก:

1. Technical signal
2. Trend strength
3. Momentum
4. Volume / price action
5. News tone
6. Business importance
7. Risk flags
8. Opportunity score

ระบบต้องส่งเฉพาะ:

- ตัวที่เข้าเกณฑ์มากที่สุด
- ตัวที่ข่าวมีน้ำหนัก
- ตัวที่กราฟมี momentum
- ตัวที่มีธุรกิจสำคัญต่ออนาคต
- ตัวที่น่าติดตามต่อ ไม่ใช่ตัวที่แค่เด้งสุ่ม

ห้ามส่งเยอะจนกลายเป็น noise

---

## 3. รูปแบบ Telegram ที่ต้องการ

แต่ละรอบต้องส่งไม่เกิน 10 ตัว และต้องเรียง:

```text
#1 = ตัวที่แรงสุด / น่าสนใจสุด
#2 = รองลงมา
...
#10 = ตัวที่ยังน่าสนใจ แต่ต่ำกว่าอันดับก่อนหน้า
```

แต่ละหุ้นต้องมี:

- `📌 Ticker + Company`
- `🏢 ทำอะไร`
- `🧩 จำเป็นต่ออะไร`
- `🧠 Technical score + opportunity score`
- `🔮 โอกาสขึ้น`
- `📈 Trend`
- `💰 ราคาล่าสุด / % change`
- `📊 Indicator summary`
- `✅ เหตุผลที่เข้าระบบ`
- `📰 ข่าวนำ`
- `🧾 สรุปข่าว`
- `🧠 วิเคราะห์ข่าว`
- `⚠️ ความเสี่ยง`

ข้อความต้องอ่านง่าย ไม่ยาวจน Telegram ตัดท้าย และถ้ายาวต้องแบ่งเป็นหลาย message โดยอันดับต้องต่อเนื่อง

---

## 4. การตีความ “น่าซื้อ / น่าลงทุน”

ห้ามใช้คำฟันธง:

- ห้ามเขียนว่า “ขึ้นแน่”
- ห้ามเขียนว่า “ต้องซื้อ”
- ห้ามเขียนว่า “กำไรแน่นอน”
- ห้ามเขียนว่า “ถือแล้ว 100-200% แน่”

ให้ใช้คำเหล่านี้แทน:

- “น่าจับตามองมาก”
- “มีโอกาสขึ้นสูงถ้า momentum ต่อ”
- “ควรรอ confirm จาก volume/ราคา”
- “เหมาะศึกษาต่อก่อนตัดสินใจ”
- “มี catalyst แต่ต้องระวัง valuation/ความผันผวน”

ระดับโอกาสขึ้น:

| ระดับ | ความหมาย |
|---|---|
| สูงมาก | กราฟแข็ง ข่าวหนุน ไม่มี risk flag หลัก แต่ยังต้องมี stop-loss |
| สูง | มี momentum และ catalyst ชัด ควรจับตา breakout/follow-through |
| ปานกลางถึงสูง | เริ่มดี แต่ต้องรอ volume หรือข่าวยืนยัน |
| เริ่มน่าสนใจ | ยังไม่ควรรีบ ต้องติดตามต่อ |
| ยังไม่เด่น | ไม่ควรเร่งตัดสินใจ |

---

## 5. Data Integrity

หลักห้ามเดา:

- ราคาล่าสุดต้องมาจาก provider ปัจจุบัน
- ข่าวต้องมาจาก feed/source ที่ดึงได้จริง
- ถ้าข่าวไม่มี ให้บอกว่า “ยังไม่พบข่าวจาก feed ที่ใช้”
- ถ้าราคาดึงไม่ได้ ให้ skip ticker นั้น ไม่ให้ bot ล้มทั้งระบบ
- ถ้าข้อมูลไม่พอ ห้ามสรุปมั่นใจเกินหลักฐาน

ข้อจำกัดที่ต้องจำ:

- Yahoo/yfinance อาจ delay, error หรือไม่มีข้อมูลบาง ticker
- บาง ticker เปลี่ยนชื่อ เช่น `SQ` ปัจจุบันคือ `XYZ`
- หุ้นบางตัวมี class share เช่น `BRK-A`, `BRK-B`
- ข่าวบางข่าวอาจเป็นกลางแต่ market ตีความแรง ต้องดู price action ประกอบ

---

## 6. Technical Framework

ใช้ technical เป็นตัวกรอง ไม่ใช่คำทำนาย

ตัวชี้วัดหลัก:

- SMA20 / SMA50
- RSI
- MACD
- ADX
- ATR
- Bollinger position
- Distance from 60-day high
- Trend label
- Volume / breakout behavior ถ้ามีข้อมูล

สัญญาณที่ดี:

- ราคาอยู่เหนือ SMA20 และ SMA50
- MACD แข็งกว่า signal
- ADX บอก trend มีแรง
- RSI ยังไม่ overbought เกินไป
- ใกล้ breakout แต่ยังไม่ไล่ราคาจนเสี่ยง
- ข่าวบวกสอดคล้องกับกราฟ

สัญญาณที่ต้องระวัง:

- ATR สูงมาก
- ราคาโดดแรงหลายวันติด
- ใกล้ ATH แต่ข่าวไม่หนุน
- RSI ร้อนเกิน
- ข่าวลบแต่ราคายังไม่สะท้อน
- Volume ขึ้นแบบ climax

---

## 7. News Analysis Framework

ข่าวต้องถูกแปลเป็นผลต่อหุ้น:

### ข่าวบวกแรง

ตัวอย่าง:

- เพิ่ม guidance
- รายได้/กำไรดีกว่าคาด
- ได้สัญญาใหญ่
- product demand โต
- analyst upgrade จากเหตุผลพื้นฐาน
- regulatory approval

ผลที่ควรเขียน:

> ข่าวนี้อาจเป็น catalyst เพิ่มแรงซื้อ ถ้าราคายืนได้และ volume ตามต่อ

### ข่าวกลาง

ตัวอย่าง:

- ข่าวทั่วไป
- commentary ไม่มีตัวเลข
- ข่าวซ้ำที่ตลาดรู้แล้ว

ผลที่ควรเขียน:

> ข่าวยังไม่ใช่ catalyst หลัก ต้องใช้กราฟและ volume ยืนยัน

### ข่าวลบ

ตัวอย่าง:

- guidance ต่ำลง
- margin แย่
- lawsuit
- downgrade
- supply chain risk
- insider selling ที่มีนัยสำคัญ

ผลที่ควรเขียน:

> ข่าวนี้อาจกด upside หรือทำให้ความผันผวนสูง ต้องลดความมั่นใจของ signal

---

## 8. Business Importance Framework

ทุกหุ้นต้องตอบให้ได้ว่า “จำเป็นต่ออะไร”

ตัวอย่าง mapping:

- Semiconductor / AI chip -> โครงสร้างพื้นฐาน AI และ data center
- Cloud / Software -> ระบบดิจิทัลขององค์กร
- Bank / Finance -> credit, liquidity, payment, capital market
- Payment Network -> โครงสร้างพื้นฐานการชำระเงินโลก
- Logistics -> supply chain และ e-commerce
- Defense / Aerospace -> ความมั่นคงและอุตสาหกรรมการบิน
- Healthcare -> ยา บริการสุขภาพ และ quality of life
- Telecom / ICT -> connectivity และ digital economy

ถ้าระบบตอบไม่ได้ ให้เขียนว่า:

> ธุรกิจอยู่ในกลุ่มที่คัดไว้ แต่ควรอ่านรายละเอียดบริษัทเพิ่มก่อนตัดสินใจ

---

## 9. Risk Management

ก่อนซื้อจริงต้องตอบให้ได้:

```text
Investment Thesis:
Entry Zone:
Invalidation / Stop-loss:
Target 1:
Target 2:
Risk per trade:
Position size:
R/R:
เหตุผลที่ยอมซื้อ:
เหตุผลที่จะไม่ซื้อ:
```

กฎหลัก:

- ห้ามซื้อเพราะ Telegram แจ้งเตือนอย่างเดียว
- ต้องมี stop-loss ก่อนซื้อ
- R/R ควรอย่างน้อย 1:2
- ถ้าราคาวิ่งแรงเกินไป ให้รอ pullback หรือ base ใหม่
- ถ้ามีข่าวดีแต่กราฟไม่ follow-through ให้รอดู
- ถ้ามีกราฟดีแต่ข่าวลบแรง ให้ลดความมั่นใจ

---

## 10. User Workflow

### ทุกวัน / ทุกครั้งที่ bot แจ้ง

1. อ่านอันดับ `#1-#10`
2. ดูว่าแต่ละตัวทำอะไร
3. ดูว่าเหตุผลมาจากกราฟหรือข่าว
4. เลือกเฉพาะ 1-3 ตัวที่น่าสนใจที่สุดไปศึกษาเพิ่ม
5. เปิดกราฟจริงดู timeframe ที่ต้องการ
6. หา entry/stop/target เองก่อนซื้อ

### ถ้าจะถาม AI ต่อ

ใช้คำสั่ง:

```text
Analyze [ticker]
```

AI ต้องตอบ:

- ธุรกิจ
- ทำไมถึงน่าสนใจ
- ข่าวล่าสุดมีผลอย่างไร
- กราฟอยู่จุดไหน
- upside/downside scenario
- entry zone
- stop-loss
- target
- bear case
- final checklist

---

## 11. Response Style

คำตอบต้องเป็นภาษาไทย อ่านง่าย และใช้ emoji พอดี

รูปแบบที่ต้องการ:

```text
TL;DR:
...

คะแนนรวม:
...

ทำอะไร:
...

ทำไมจำเป็น:
...

กราฟ:
...

ข่าว:
...

โอกาสขึ้น:
...

ความเสี่ยง:
...

แผนที่ควรดูต่อ:
...
```

ห้ามตอบแบบยาวพร่ำ ถ้าเป็น Telegram ต้องกระชับ แต่ครบพอให้ตัดสินใจคัดต่อได้

---

## 12. Bot Operations

คำสั่งเช็ก bot:

```bash
./scripts/status_launch_agent.sh
```

เช็ก process:

```bash
ps -p $(launchctl print gui/$(id -u)/com.kasidit.stock-news-alert | awk '/pid =/ {print $3}') -o pid,lstart,etime,command
```

เช็ก config runtime:

```bash
grep '^TOP_ALERTS_PER_RUN=' ~/.stock-news-alert/.env
grep '^STOCK_GROUPS=' ~/.stock-news-alert/.env
```

ดู log:

```bash
tail -n 80 ~/.stock-news-alert/logs/stock-news.err.log
```

restart:

```bash
./scripts/install_launch_agent.sh
```

---

## 13. Final Mandate

ระบบนี้ต้องช่วยให้ผู้ใช้:

- ไม่พลาดหุ้นที่เริ่มแรง
- ไม่โดน noise จากหุ้นเยอะเกินไป
- เข้าใจว่าบริษัททำอะไร
- เข้าใจว่าข่าวมีผลต่อราคายังไง
- มีกรอบคิดก่อนซื้อ
- ไม่ตัดสินใจด้วย FOMO
- ใช้ bot เป็น radar ไม่ใช่ autopilot

> **Final Rule:** Bot คัดหุ้นให้เร็วขึ้นได้ แต่การซื้อจริงต้องผ่าน thesis, entry, stop-loss, target และ risk sizing เสมอ

---

*PERSONAL STOCK INVESTOR SOP · Kasidit Edition · May 2026 · Confidential*
