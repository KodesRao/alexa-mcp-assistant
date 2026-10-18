# Alexa+ Built-in Features: How They Work and Limitations

Last updated: Oct 18, 2026

Research notes for the Build, Ship, Shape hackathon (Alexa+ track). Based on public information and general knowledge; Amazon does not publish every internal detail.

| # | Feature | What it does and how it works | What the user must set up | Limitations | Opportunity |
| --- | --- | --- | --- | --- | --- |
| 1 | Natural conversation | Voice goes to the cloud and is turned into text. A large language model understands it and writes a reply, which is turned back into speech. | Echo device or Alexa app, internet, Amazon account | Needs internet; short delay; can mishear accents or mixed languages such as Manglish; can sound confident while wrong | Local-language or Manglish-friendly helpers |
| 2 | Smart home control | Devices connect by Wi-Fi or a hub (Zigbee, Matter). The maker's cloud links to Alexa through a smart home skill. Alexa sends commands to that cloud, which tells the device. Routines are saved command lists. | Supported devices, maker's app, account linking in the Alexa app | Supported brands only; fiddly setup; fails if the maker's cloud is down; weak local-brand support; no safety judgment | Safety checks before risky actions |
| 3 | Timers, alarms, reminders, calendar | Timers run on the device and in the cloud. Calendars connect through linked Google, Outlook, or Apple accounts. | Link calendar accounts | Weak at complex scheduling; work calendars often blocked | Smarter scheduling helpers |
| 4 | Music, podcasts, news | Calls streaming services through linked accounts. News comes from partner publishers. | Link streaming accounts; sometimes a paid plan | Premium plans often needed; vague requests miss; limited news sources | Low fit |
| 5 | Shopping on Amazon | Searches Amazon's catalog using your account, address, and Prime status. Shows price and delivery, reorders, tracks price drops. | Amazon account with address and payment method | Mostly Amazon-only; cannot verify genuine products or sellers; no fair outside price comparison; blind to scams on social media and outside websites | ShopShield: scam and counterfeit checks for deals outside Amazon |
| 6 | Booking and errands | Partner services connect through APIs (MCP, agent skills). Alexa fills in details and calls them. | Link partner accounts | Only partners that joined; mostly US-focused; weak in Malaysia; unusual requests fail; little visibility into bookings | Checks that a booking or seller is legitimate |
| 7 | Remembering personal details | Stores facts you share in your Amazon account and uses them later. | Tell Alexa facts or allow memory | Can remember wrongly or out of context; privacy concerns; weak family sharing | Low fit |
| 8 | Reading documents and emails | Reads forwarded emails or uploaded files, pulls out dates and tasks, saves reminders or events. | Forward emails or upload files | Misreads messy scans; does not detect phishing or fake invoices | Strong option: phishing and fake-invoice checker |
| 9 | Ring camera summaries | Ring cameras upload video to Ring's cloud; AI detects people, packages, and vehicles; Alexa reads summaries. | Ring device and Ring subscription | Subscription needed; can mislabel events; describes but does not judge suspicious behaviour | Delivery-scam or suspicious-visit alerts (Ring track) |

## Key pattern

Alexa+ is strong at doing things but weak at judging trust. It cannot tell whether a deal, seller, email, or invoice is a scam, or whether a product is fake. Rows 5 and 8 are the strongest fits for a trust and safety project.

## Hackathon project ideas

| Idea | Already available in Alexa+ | What could be added | Implications and challenges |
| --- | --- | --- | --- |
| **1. Mood and health companion** |<br>• **Reminders** for medicine and daily tasks<br>• **Amazon One Medical** linked with Alexa+<br>• **General wellness chat**<br>• **Routines** |<br>• **Daily mood check-ins**<br>• **Mood-based suggestions** (music, activities, routines)<br>• **Symptom check** that points to a doctor<br>• **Follow-up** after a doctor visit<br>• **Medicine tracking** with dose confirmation |<br>• **Medical risk** if advice is wrong<br>• **Heavily regulated,** unclear liability<br>• **Highly sensitive data** (health and mood)<br>• **Shared devices** expose private data<br>• **Emotional safety** needs expert design<br>• **Weak fit** with trust and safety skills<br>• **Hard to finish** before the deadline |
| **2. ShopShield: web-wide deal search and scam protection** |<br>• **Linked Amazon account**<br>• **Product search** on Amazon<br>• **Price, delivery, order history**<br>• **Reorders and price-drop alerts**<br>• **Voice purchase** with optional PIN |<br>• **Web search** across marketplaces, social posts, second-hand sites and shops (no account linking)<br>• **Price baseline**: official brand price first, market middle as fallback<br>• **Fake-price flag** when far below the baseline<br>• **Legitimacy check** for sellers and listings<br>• **Scam flags** for social media and unknown sites<br>• **Unsafe payment warnings**<br>• **Spoken verdict** naming the baseline used<br>• **Future step**: platform account linking |<br>• **Login-walled posts** (Facebook, Carousell) often missing from search<br>• **Short snippets**, so pages may need opening, which is slower<br>• **Out-of-date results** (sold items, changed prices)<br>• **Brand sites** may block bots or not sell the model locally<br>• **Low price is not proof** of a fake (sales, second-hand)<br>• **False positives** can hurt honest sellers<br>• **Never accuse sellers,** only report risk signals |

## Updated ShopShield approach

### Web search instead of linking platform accounts

Instead of linking Shopee, Lazada and other accounts, ShopShield searches the whole web for the product the user asks about.

1. **User asks Alexa,** for example "find me a good Adidas jogging shoe."
2. **Alexa calls the ShopShield helper** through MCP.
3. **The helper uses a web search API** (such as Tavily, Brave Search or Google's search API) to gather listings from marketplaces, Facebook posts, second-hand sites and online shops.
4. **Each listing is checked** for scam and counterfeit signs.
5. **Alexa reads back the safest options** with short warnings for risky ones.

**Why web search:**

- **Buildable by the deadline:** needs only one search API key, no platform approvals.
- **Better fit for scams:** most scams sit outside the big platforms, in social posts, ads and unknown sites.
- **Better pitch to Amazon judges:** framed as protection, not sending users to competitors.

**Limits:**

- **Facebook and Carousell posts** behind a login often don't appear in search.
- **Snippets are short,** so pages may need to be opened for full price and seller details, which is slower.
- **Results can be out of date** (sold items, changed prices).
- **Future step:** account linking for exact prices, stock and order history.

### Price baseline (fake-price check)

A fallback chain sets the "normal" price to compare listings against:

1. **Official brand price:** search only the brand's official site (for example adidas.com.my) for the model. The price comes from the snippet or by opening the page. No special brand access is needed.
2. **Market middle (fallback):** if no official price is found (model not sold locally, out of stock, site blocks bots), take the median price across search results after dropping extreme outliers.
3. **No baseline:** if both fail, skip the price judgement, rely on other warning signs, and tell the user the price couldn't be checked.
4. **Compare:** flag a listing as risky if it is far below the baseline (for example under 40 to 50% of it).
5. **Explain:** Alexa says which baseline was used, for example "compared with Adidas's official price of RM459."

**Notes:**

- **Rejected: a hand-built reference price list.** Too many products to cover, and genuine prices are hard to confirm.
- **A low price alone is not proof of a fake.** Clearance sales and second-hand items can be legitimately cheap, so price is one signal alongside unsafe payment, replica wording and suspicious domains.
- **Planned code change:** a new "get price baseline" tool that the deal checker calls first.
