# Riot Stars — Translation Glossary

Paste this into every translation session, directly under `translation_prompt.md`.

**Every entry here is fixed.** Use the English form exactly as written, everywhere, forever. To
change one, follow §4.3 of the prompt: state the correction explicitly and list every previously
translated line that must be revisited.

Entries in **§9 PROVISIONAL** are *not* decisions — they are names seen in the dumps but not yet
rendered in any translated line. Promote one to its proper table the first time you use it.

Status: covers `script_unique.txt` lines 1–52 (unit/class descriptions) and `battle_dump.txt`
chunks **0, 10, 11, 12, 14, 34, 35, 40** (prologue + all of tier E).

---

## 1. People

| Japanese | English | Note |
|---|---|---|
| カイン | Kain | main companion; casual register, contractions throughout |
| リムル | Rimul | enemy commander, female, addressed as 様 → **Ｌａｄｙ　Ｒｉｍｕｌ**; formal, unhurried register |
| ドースン | Dawson | enemy officer, defeated before/around chunk 0 |
| レンドル | Rendol | Rimul's subordinate |
| セネカ | Seneca | craftsman |
| ファリーナ | Farina | |
| フィリス | Phyllis | |
| フェルナンド | Fernando | commander of the 2nd Royal Army |
| ギルフォード | Guilford | |
| アルフレッド | Alfred | 少尉 → **Ｓｅｃｏｎｄ　Ｌｉｅｕｔｅｎａｎｔ　Ａｌｆｒｅｄ**; orders Beatrice to the 9th Army (ch.14) |
| アルテミス | Artemis | |
| リッジ | Ridge | party member; snarky, blunt, casual. Also `script_unique` 1366 |
| マヤ | Maya | forest witch (ch.11), spareable; later a shopkeeper (`script_unique` 1348–1350) |
| シロン | Shiron | martial artist, master of the Caucasus dojo, joins the party (ch.12). Alt readings *Sylon*, *Chiron* — Shiron chosen as the plainest |
| ベアトリス | Beatrice | captain, Carline 7th Army 3rd Squad; joins in ch.14 |
| カシム | Kasim | ch.34 boss, portrait 7 — speaks first |
| タシム | Tasim | ch.34 boss, portrait 8 — his brother. The near-identical names are the joke; keep them near-identical |
| リオン | **unresolved — Lion or Leon** | pick on first use and record here |
| 王女様 | the Princess | |
| 神父 | priest | the fairy's ring-bearer |
| 妖精 | fairy | lowercase, common noun; referred to as *she* |
| 市長 | the mayor | Caucasus (ch.12); also `script_unique` 380 |

## 2. Factions, places, ranks

| Japanese | English | Note |
|---|---|---|
| 第９軍 / ９軍 | 9th Army | the player's unit; `９` is full-width in source |
| 第７軍 | 7th Army | Alfred's; `７` full-width, same rule |
| 第３分隊 | 3rd Squad | `３` full-width |
| 分隊長 | squad captain | promoted from PROVISIONAL. Use **squad captain** where 隊長 is written out (ベアトリス, ch.14), **squad leader** for the bare 分隊長 |
| 隊長 | captain | how the player character is addressed. `Ｃａｐｔａｉｎ　{FC00}` = 15 columns; `Ｃｏｍｍａｎｄｅｒ` does not fit alongside the insert |
| 少尉 | Second Lieutenant | 18 columns — will not share a line with a name |
| 宮廷軍 / 宮廷防衛軍 | Royal Army / Royal Defence Force | keep the two distinct |
| 紅の騎士団 | Crimson Knights | elite imperial unit |
| 帝国 | the Empire | 帝国軍 → the Empire's men where 24 columns will not take "the Imperial army" |
| 精鋭部隊 | elite corps | the Crimson Knights' formation |
| 本隊 | the main force | distinct from 精鋭部隊 |
| カーライン | Carline | home castle/territory |
| カーライン王国 | Kingdom of Carline | |
| カーライン城 | Carline Castle | |
| クリミア | Crimea | region |
| コーカサス | Caucasus | town of martial artists; Shiron's dojo is here |
| バウワーの砦 | Bauer's fort | ch.40. Alt *Bower*; Bauer chosen as the likelier source reading |
| バジリスクの砂漠 | the Basilisk Desert | ch.14 map. Capitalised only as the place name — the monster stays lowercase |
| ホビット / ホビットの村 | Hobbit / Hobbit Village | |
| 龍人族 | dragonfolk | one word, 11 columns. Will not fit a ≤20 class slot as "Dragonfolk descendant" — flag if it is ever needed there |
| トカゲ | lizard | 〜さん as address → **Ｍｉｓｔｅｒ　Ｌｉｚａｒｄ** |
| 司令部 | headquarters | 12 columns — only fits alone on a line |
| 守備兵 | garrison / garrison men | seed had "garrison soldier"; 8+8 columns rarely fits, so bare **garrison** is the default and **garrison men** the plural-personal form |
| 機械兵 | machine soldier | |
| 援軍 | reinforcements / **aid** | use "aid" only where 24 columns will not take the full word; flag each time |
| 要塞 | fortress | 8 columns |
| 旗印 | banner | |
| 死罪 | death (as a penalty) | 逃亡は死罪 → `Ｆｌｉｇｈｔ　ｂｅｆｏｒｅ　ｔｈｅ　ｅｎｅｍｙ　ｍｅａｎｓ　ｄｅａｔｈ` |

## 3. Items and mechanics

| Japanese | English | Note |
|---|---|---|
| ジュエル | Jewel | currency; **do not** translate as "gem" |
| ジェム / 『ジェム』 | Gem / “Ｇｅｍｓ” | battle pickup — distinct from Jewel, keep both |
| ジェムタイプ | Gem Type | 2,964 occurrences — never vary it |
| 緑 / 赤 / 青 (Gem Type) | Green / Red / Blue | |
| サイクル / ランダム (Gem Type) | Cycle / Random | |
| パワーストーン / 『パワーストーン』 | “Ｐｏｗｅｒ　Ｓｔｏｎｅ” / “Ｐｏｗｅｒ　Ｓｔｏｎｅｓ” | `『…』` → `“…”` |
| 必殺技 | special attack | |
| 指輪 | the ring | plot item |
| 玉 (ジェムの) | orbs | the small red and green drops |
| ユニット / クラス / クラスチェンジ | unit / class / class change | |
| 待ち時間（Ｗａｉｔ） | Ｗａｉｔ　ｔｉｍｅ | the parenthetical gloss is redundant in English — drop it |
| ＨＩＴ | hits | source uses full-width caps for the loanword; English needs no emphasis |
| ○ボタン / □ボタン | Ｃｉｒｃｌｅ　ｂｕｔｔｏｎ / Ｓｑｕａｒｅ　ｂｕｔｔｏｎ | ○ □ are outside the permitted charset |

## 4. Classes and class descriptions

| Japanese | English | Note |
|---|---|---|
| 剣士 / 女剣士 | swordsman / swordswoman | 女 marks the female classes |
| 戦士 | warrior | |
| 弓兵 / 弓の戦士 | archer / bow warrior | |
| 軽騎兵 | light cavalry | |
| 騎士 | knight | |
| 天馬騎士 | pegasus knight | lowercase — a class noun, not a name |
| 魔術師 / 女魔術師 | mage / sorceress | "sorceress" only where 女 is explicit |
| 魔法戦士 / 魔法騎士 | magic warrior / magic knight | keep the two distinct |
| 盗賊 | thief | |
| 武闘家 | martial artist | lowercase in prose; `Ｍａｒｔｉａｌ　Ａｒｔｉｓｔ` = 14, fits the ≤20 class cap |
| バジリスク | basilisk | monster common noun, lowercase; capitalised only in the Basilisk Desert |
| フリーナイト | Free Knight | capitalised — a named class |
| ビーストマスター | Beast Master | two words, capitalised |
| 昇格型 | promoted | → "a promoted X"; distinct from 上級 |
| 上級 / 上級職 / 最上級 | advanced / advanced class / highest‐class | three distinct tiers, never interchange |
| 全体魔法 / 単体魔法 | all‐target magic / single‐target magic | uses ‐ (U+2010) |
| 炎 / 雷 / 氷 / 暗黒 / 光 / マヒ | fire / thunder / ice / dark / light / paralysis | **雷 = thunder**, not lightning — 9 columns will not fit |
| 攻撃力 / 防御力 / 機動力 / 戦闘力 | attack power / defence power / mobility / combat power | British spellings (defence, armour) throughout |
| 一撃必殺 | kills with one blow | |
| 山林 | woodlands | |
| クラスＮＮ | Ｃｌａｓｓ　ＮＮ | untranslated placeholder slots 41–43; digits stay full-width |
| ダミーぶきです | Ｔｈｉｓ　ｉｓ　ａ　ｄｕｍｍｙ　ｗｅａｐｏｎ． | unused placeholder, 126× |
| ダミーぼうぐです | Ｔｈｉｓ　ｉｓ　ａ　ｄｕｍｍｙ　ａｒｍｏｕｒ． | unused placeholder, 84× |

## 5. Verbal tics — decided, never mix

| Japanese | English | Note |
|---|---|---|
| ノロ (sentence-final) | trailing **`，ｎｙｏｒｏ．`** | hobbit shopkeeper. Appended to the final clause of each sentence, replacing that sentence's own full stop. Mechanical by design, so duplicated lines stay byte-identical |
| ゲロゲロ | **`Ｒｉｂｂｉｔ`** + the source's own punctuation | **not only the frog merchant** — the ch.10 lizardmen use it too, and the punchline of that chunk turns on it. The *word* is fixed; the stop that follows is whatever the source has (`。` → `．`, `！` → `！`), and inside the ch.10 joke it is quoted: `“Ｒｉｂｂｉｔ”` |
| katakana speech (lizardmen, frog merchant) | blunt, article-dropping English | `オ前タチ、強イカラ` → `Ｙｏｕ　ｓｔｒｏｎｇ，　ｓｏ`. Drop articles always; drop the copula in short predicative statements; keep the verb where a negation needs it (`Ｗｅ　ａｒｅ　ｎｏｔ　ｌｉｚａｒｄｓ．`) |

## 6. Stock phrases and interjections

| Japanese | English | Note |
|---|---|---|
| 命拾いしたな | Ｙｏｕ　ｋｅｅｐ　ｙｏｕｒ　ｌｉｖｅｓ．．． | recurs across chunks — match it every time; preserve each instance's own dot count |
| よし、次はコーカサスだ。先を急ごう！ | `Ｒｉｇｈｔ，` / `Ｃａｕｃａｓｕｓ　ｉｓ　ｎｅｘｔ．` / `Ｌｅｔ’ｓ　ｈｕｒｒｙ　ｏｎ！` | three `{FFFE}` segments. 4 occurrences across chunks 10 and 11 — verified byte-identical |
| 私たち沼を侵したりするつもりはなかった | `Ｗｅ　ｎｅｖｅｒ　ｍｅａｎｔ　ｔｏ` / `ｉｎｔｒｕｄｅ　ｏｎ　ｙｏｕｒ　ｓｗａｍｐ．` | ch.10, 3 occurrences across two speakers; the `の` / `のよ` variants get the same English |
| ソノ事、モウ気ニシナイ。… | `Ｔｈａｔ　ｍａｔｔｅｒ，　ｆｏｒｇｏｔｔｅｎ．` / `Ｙｏｕ　ｓｔｒｏｎｇ，　ｓｏ` / `ｗｅ　ｗｅｌｃｏｍｅ　ｙｏｕ．` / `Ｃｏｍｅ　ｂｙ　ａｎｙ　ｔｉｍｅ．` | ch.10, 2 occurrences |
| 俺たちは兄弟。… | `Ｗｅ　ａｒｅ　ｂｒｏｔｈｅｒｓ．` / `Ｔｏｇｅｔｈｅｒ　ｉｎ　ａｌｌ　ｔｈｉｎｇｓ！` / `Ｉｎ　ｌｉｆｅ　ａｎｄ　ｉｎ　ｄｅａｔｈ．` | ch.34, 2 occurrences |
| ・・・・！？ | ．．．．！？ | ch.10 and ch.11, 2 occurrences |
| ムムッ | Ｈｍｐｈ | grunt |
| ふっ / フンッ | Ｈｍｐｈ | both scoffs collapse to the same English — deliberate |
| ほう | Ｈｏｈ | impressed grunt; **distinct** from the Ｈｍｐｈ pair. ⚠️ see §10.6 |
| む | Ｈｍ | shorter, more sceptical grunt (ch.12) |
| まったく | Ｒｅａｌｌｙ， | exasperation / contempt |
| ふう | Ｐｈｅｗ， | relief |
| グッ / ぐわっ | Ｇｕｈ / Ｇｗａｈ | pain, then the death cry |
| はっ (military assent) | Ｓｉｒ | a recruit answering an officer |
| いいな！！ / わかったなっ！！ | Ｇｏｔ　ｉｔ！！ / Ｇｏｔ　ｔｈａｔ！！ | keep the two distinct, they are different source strings. **Do not** use either for a plain 分かった — that is `Ｒｉｇｈｔ，` |
| 行くぞ！ | Ｍｏｖｅ　ｏｕｔ！ | |

## 7. Register per character

| Who | Register |
|---|---|
| Kain, the player character | casual; contractions freely (`ｄｏｎ’ｔ`, `ｉｔ’ｓ`, `ｌｅｔ’ｓ`) |
| Rimul | formal, measured, no contractions in her own lines |
| Officers addressing the 9th Army | gruff, imperative, clipped |
| Ridge | blunt and needling; the shortest line in any exchange is usually his |
| Maya | arch, coquettish; **third-person self-reference is kept in English** (`ｌｅｔ　Ｍａｙａ　ｐｌａｙ　ｗｉｔｈ　ｙｏｕ`) except where the source itself switches to 私 |
| Shiron | rough and warm; contractions, `Ｉ’ｖｅ`, `ｃａｎ’ｔ`; addresses the player informally |
| Beatrice | crisply formal, military; no contractions |
| Kasim and Tasim | simple, doubled, comic; their paired lines echo but never match exactly |
| Village elders (じゃ / のう) | plain and old-fashioned, no contractions, no archaic English spelling |
| The Caucasus mayor | polite, slightly fussy; `Ｉ　ａｍ`, not `Ｉ’ｍ` |
| Lizardmen / frog merchant | see §5 — blunt, article-dropping |
| Tutorial boxes (`{=FA1000300030}`) | plain instructional second person, no personality |

## 8. Fixed-width caps

| Table | Cap |
|---|---|
| player name (`{FC00}{=0000}`) | 7 characters — budget 7 columns wherever it appears |
| unit names | ≤ 16 half-width characters |
| class names, monster names | ≤ 20 half-width characters |

New unit-table candidates all clear the ≤ 16 cap as written: Ridge (5), Maya (4), Shiron (6),
Beatrice (8), Kasim (5), Tasim (5).

⚠️ The class *names* have not been fixed yet — §4 above covers only the description prose. Set them
before any chunk that displays a unit roster.

---

## 9. PROVISIONAL — seen in the dumps, not yet rendered

Do not treat these as decisions. Promote on first use.

| Japanese | Likely English | Where seen |
|---|---|---|
| メルザリオ | Melzario / Merzario | battle script, hobbit village-chief's son |
| ティミー | Timmy | battle script, chunk with Fernando |
| サイクス | Sykes / Cyx | same scene as ティミー |
| 宮廷第２軍 | 2nd Royal Army | Fernando's unit |
| リザードマン | Lizardman | `script_unique` 1297; the ch.10 dragonfolk are presumably this class |
| レバーク | Leverk / Rebark | `script_unique` 1350, a castle Maya has left |
| オーク | Orc | monster class |
| ブラウニー | Brownie | monster class |
| 鬼 / 悪鬼 | ogre / fiend | monster classes; 悪鬼 glossed as 豚顔 (pig-faced) |
| 巨人 | giant | monster class |

---

## 10. Open questions

1. **リオン — Lion or Leon.** Unresolved. Decide before the character appears.
2. **Class/unit name table.** Untouched; needs the ≤ 20-character forms fixed.
3. **Description window row count.** 3 or 4 rows is unconfirmed; §3.2 of the prompt keeps
   descriptions to 2 lines + Gem Type until someone checks in-game.
4. **`{FCC0}{FFFE}` leading break.** Whether it wastes a top row is unconfirmed. Preserve for now.
   Related: a page carrying a leading blank *and* four text rows *and* a trailing blank has never
   appeared in the source — tier E avoided producing one. Worth settling with the same in-game check.
5. **`ダミーぶきです` padding.** The source pads to 11 columns with trailing `　`; the English is 23
   and drops the padding. If that field turns out to be fixed-width, shorten to
   `Ｄｕｍｍｙ　ｗｐｎ．` / `Ｄｕｍｍｙ　ａｒｍ．`.
6. **`ほう` may already be rendered in chunk 0.** Rimul says `ほう・・・。` there. `Ｈｏｈ` was
   chosen for ch.35 without sight of `tl/battle/chunk_000.txt`. **Check chunk 0 and, if it differs,
   chunk 0's form wins** — revise ch.35 line 13 (`{FCD0}{=00080001…}`) to match.
7. **Player gender.** Ch.12 renders Shiron's `あんちゃん` as `ｌａｄ`, which assumes a male player
   character. If the name is free-entry with no fixed gender, swap to `ｆｒｉｅｎｄ` — same 18
   columns.
8. **Numerals in prose.** Ch.12 spells out `３時間` / `３時の鐘` as "Three hours" / "three o'clock"
   rather than keeping the full-width `３`. Both are legal charset; the digits-stay-full-width note
   in §4 covers the `ＣｌａｓｓＮＮ` placeholder slots only. Confirm the house preference before a
   chunk with many numbers.
9. **`これ以上砂は増やしたくないな`** (ch.14) is rendered literally as "I do not want to add any
   more to the sand" because it is unclear whether the sand grows by petrified victims or this is a
   figure for casualties. Check the map in-game.
10. **`訊ねたい` vs `尋ねたい`** — chunk 0 uses both spellings for the same phrase in Rimul's two
    variant speeches. Probably a source typo; it will matter to whoever dedupes chunk 0.
11. **The ch.35 mansion speaker is unnamed.** Portrait 8, confident, two lines, no name anywhere in
    the chunk. If a later chunk names him, re-check his register.

---

## 11. Added by the chunk 43 spike (tier A feasibility, chunk 43)

Rendered in `pending/chunk_043.txt`. Chunk 43 is the final chapter: the Helfer confrontation in
the sky-fortress control room, Rimul's revenge for Guilford, the self-destruct, and the airship
epilogue.

### 11.1 People

| Japanese | English | Note |
|---|---|---|
| ヘルファー | Helfer | final boss, commander of the floating island. Alt *Hellfar*; Helfer chosen to match the game's German/European naming (Bauer, Carline). 6 chars, clears the ≤ 16 unit cap |
| ティミー | Timmy | **promoted from §9 PROVISIONAL** — rendered in ch.43, where she is addressed by name and told to flee |

### 11.2 Places, factions, ranks

| Japanese | English | Note |
|---|---|---|
| フェリスランド | Ferisland | the land the island's lasers threaten. Alt *Felisland*, *Ferrisland*. Appears nowhere else in either dump — see FLAGS |
| ハイランド / 古代ハイランド | Highland / ancient Highland | the vanished civilisation that built the fortress |
| 浮遊島 | the floating island | |
| 空中要塞 | sky fortress | keep distinct from 要塞 → fortress |
| 指令官 | Commander | the source spells it 指令官, not 司令官 — treated as the same word |
| ４号機 | Ｕｎｉｔ　４ | the machine the 9th Army destroyed; digit stays full-width |

### 11.3 Items and mechanics

| Japanese | English | Note |
|---|---|---|
| 自爆装置 | ｓｅｌｆ‐ｄｅｓｔｒｕｃｔ | uses ‐ (U+2010); 13 columns |
| 解除装置 | the switch | "shutoff device" is 15 columns and will not share a line — **switch** is the fixed short form |
| レーザー兵器 | lasers / laser weapons | |
| コントロール室 | control room | |

### 11.4 Classes

| Japanese | English | Note |
|---|---|---|
| 魔導師 | wizard | Guilford. Distinct from 魔術師 → mage and 女魔術師 → sorceress |

### 11.5 Tics and interjections

| Japanese | English | Note |
|---|---|---|
| くっ / クッ | Ｔｃｈ | vexation. **Distinct** from ムムッ / ふっ / フンッ → Ｈｍｐｈ and from ほう → Ｈｏｈ |
| グワアアアァァ | Ｇｗａａａａａｈ | death cry; extends the existing ぐわっ → Ｇｗａｈ |
| フハハハ… | Ｆｕｈａｈａｈａ… | Helfer's laugh; length tracks the source's kana count |
| 雑草ども | weeds | Helfer's contemptuous term for the 9th Army; recurs, keep it |
| 命の恩人 | your rescuer | 9 columns; "the man who saved you" never fits |

### 11.6 Register

| Who | Register |
|---|---|
| Helfer | grandiose and archaic, no contractions; calls the party **weeds** and **rabble**. His register is what makes him expensive to translate — see FLAGS |

---

## 12. Added by chunk 33 (the sanctuary / class-change trial)

Rendered in `tl/battle/chunk_033.txt`. Chunk 33 was missing from `battle_dump.txt` until the
dumper's `{FC51}`-only detector was fixed (`findings.md` §23) — it is the sanctuary map: an
unnamed sorceress tests the party's mage and grants the “Ｂｏｏｋ　ｏｆ　Ｋｎｏｗｌｅｄｇｅ”.

### 12.1 Places and items

| Japanese | English | Note |
|---|---|---|
| 聖堂 | sanctuary | 9 columns. Not “cathedral” / “sacred hall” — both are too wide to share a line and the place is a mages' preserve, not a church |
| 『知識の書』 | “Ｂｏｏｋ　ｏｆ　Ｋｎｏｗｌｅｄｇｅ” | `『…』` → `“…”`; 20 columns with the quotes, so it never shares a line with anything but a short article |
| 魔道の力 | the power of magic | 魔道 here is the art, not a person — do not confuse with 魔導師 |

### 12.2 Classes

| Japanese | English | Note |
|---|---|---|
| ウィザード | Ｗｉｚａｒｄ | **capitalised** — a named class, like フリーナイト → Free Knight. The advanced class a 魔術師 changes into. ⚠️ collides with 魔導師 → wizard from §11.4 — see §13.12 |

### 12.3 Tics and interjections

| Japanese | English | Note |
|---|---|---|
| ふふ | Ｆｕｆｕ | soft, amused feminine chuckle. Transliterated to match フハハハ → Ｆｕｈａｈａｈａ (§11.5). **Distinct** from ムムッ/ふっ → Ｈｍｐｈ and ほう → Ｈｏｈ. Alt `Ｈｅｈ　ｈｅｈ` — see FLAGS |

### 12.4 Register

| Who | Register |
|---|---|
| The sanctuary sorceress (ch.33) | poised and imperious, no contractions; `Ｉ　ｓｈａｌｌ`, `Ｖｅｒｙ　ｗｅｌｌ`, `Ｃｏｍｅ　ａｔ　ｍｅ`. Close to Rimul's register but warmer once the party wins — she is a teacher, not an enemy. Unnamed in this chunk |
| Deployment-restriction boxes (`{=FA1000300030}`) | as §7 tutorial boxes — plain instructional second person, no personality |

---

## 14. Added by chunks 5 and 7 (the fairy forest; the Black Knights and Nacol)

Chunk 7 is rendered in `tl/battle/chunk_007.txt`. Chunk 5 is rendered in
`pending/chunk_005.txt` and **does not ship** — it misses its slot by 487 bytes (see
`FLAGS.md` and `pending/README.md`). The names below are decided regardless, because
chunk 7 uses several of them and later chunks will use the rest.

### 14.1 People

| Japanese | English | Note |
|---|---|---|
| キャビア | Ｃａｖｉａ | The Princess's given name, first revealed here (ch.5 `キャビア王女`, ch.7 `キャビア様`). 5 columns, so `Ｐｒｉｎｃｅｓｓ　Ｃａｖｉａ` fits at 15. Alt *Caviar*, *Kyabia* — Cavia chosen as the plainer name-like form, matching Bauer / Carline / Helfer. ⚠️ see §13.14 |
| フェイ | Ｆｅｉ | Female 氷龍使い, warden of the fairy forest; joins the party in ch.5 |
| ナコール | Ｎａｃｏｌ | Cavia's aged former tutor (ch.7). Alt *Nakor*, *Nacoll*. ⚠️ see §13.15 |
| ティータ | Ｔｉｔａ | ch.5 line 1, `ティータ、合流して。戦うわよ。` — **one occurrence in the whole battle dump, zero in the script dump**. ⚠️ see §13.16 |
| フィリス様 | Ｌａｄｙ　Ｐｈｙｌｌｉｓ | 様 → Lady per the Rimul precedent. ch.5 reveals Phyllis is the 妖精の村の長. Does **not** change her §1 entry — only adds the honorific form |

### 14.2 Places, factions, ranks

| Japanese | English | Note |
|---|---|---|
| 黒の騎士団 | Ｂｌａｃｋ　Ｋｎｉｇｈｔｓ | Parallels 紅の騎士団 → Crimson Knights. 13 columns |
| ベルナールの教会 / ベルナール教会 | Ｂｅｒｎａｒｄ’ｓ　ｃｈｕｒｃｈ | Possessive form per バウワーの砦 → Bauer's fort. Alt *Bernal* |
| 妖精の森 | the fairy forest | 妖精 stays a lowercase common noun (§1) |
| 番人 | warden | Fei's role. Kept **distinct** from 守り神 → guardian |
| 守り神 | guardian | The forest's tutelary spirit, not a person |
| 妖精の村の長 | village elder | Phyllis's title |

### 14.3 Classes and roles

| Japanese | English | Note |
|---|---|---|
| 氷龍使い | ice dragon tamer | |
| 獣使い | beast tamer | 使い → *tamer* throughout, not *user* / *handler* |
| オーク | orc | **Promoted from §9 PROVISIONAL.** Lowercase common noun in prose, per the バジリスク → basilisk precedent. The class-table form is still open (§10.2) |
| 機械兵 | machine soldier | Unchanged from §4; recorded here because ch.7 is its first rendering |

### 14.4 Items and figures of speech

| Japanese | English | Note |
|---|---|---|
| 嘘ツキ先生 | the lying teacher | ch.7. Nacol, who lied about being cured to send Cavia home; the falling stars are read as his bouquet |
| 切り札 | ace | `帝国の切り札` → *their ace*. Not “trump card” — 11 columns saved and no card-game register in English |
| エチュード | etude | **No `é`** — the accented form is outside the §3.1 charset |
| ゴミ (as an insult) | rubbish | British, consistent with the existing spelling policy |

### 14.5 Tics and interjections

| Japanese | English | Note |
|---|---|---|
| クックックッ | Ｋｕｋｕｋｕ | Cold, clipped villain laugh. Kana beats tracked, as with フハハハハ → Ｆｕｈａｈａｈａ (§11.5) |
| ククククク | Ｋｕｋｕｋｕｋｕｋｕ | Same laugh, five beats — the length is doing work, so it is preserved |
| フハハハハハ | Ｆｕｈａｈａｈａｈａｈａ | Five ハ. Extends §11.5's four-beat entry; the entry itself is unchanged |
| ぐふっ | Ｇｕｆｆ | Struck-down grunt. Distinct from グッ → Ｇｕｈ and ぐわっ → Ｇｗａｈ (§11.5) |
| へっ | Ｈｅｈ | Ridge's cocky scoff. Distinct from ふっ / フンッ → Ｈｍｐｈ |
| ゴホッ | Ｃｏｕｇｈ | Nacol's sickbed cough. Rendered as an English word, not transliterated — `Ｇｏｈｏ` reads as a name |
| ええい | Ｅｎｏｕｇｈ！ | Exasperated officer's bark |
| うひょーっ | Ｗｈｏａａ！ | Delighted whoop |

### 14.6 Register

| Who | Register |
|---|---|
| Cavia (the Princess) | Warm, direct, **no contractions** — `Ｉ　ｓｈａｌｌ`, `ｌｅｔ　ｕｓ`, `Ａｒｅ　ｔｈｅｙ　ｎｏｔ`. Young and impulsive, not stiff. One deliberate exception, see `FLAGS.md` |
| Fei | Gentle but firm; light contractions. Speaks plainly about the forest and formally to Phyllis |
| Lady Phyllis | Formal, warm, maternal, no contractions |
| Nacol | Frail and deferential — `Ｌａｄｙ　Ｃａｖｉａ`, `Ｙｏｕ　ｍｕｓｔ　ｎｏｔ`. Never contracts, never commands except to send her home |
| The Black Knights commander (ch.7) | Cold and mocking; `Ｋｕｋｕｋｕ`, calls people rubbish. No contractions — the flatness is the menace |
| Anselmo-type Imperial officers (ch.7) | Blustering and superior; `Ｆｕｈａｈａｈａｈａｈａ`, rhetorical questions |

---

## 13. Open questions (continued from §10)

12. **`ウィザード` vs `魔導師`.** §11.4 fixed 魔導師 → *wizard* (lowercase, prose, for Guilford);
    §12.2 fixes ウィザード → *Ｗｉｚａｒｄ* (capitalised, the class). These are very probably the
    same class written two ways in the source. Neither entry is changed here — per §4.3 that needs
    an explicit decision. Settle it when the class-name table is fixed (§10.2), and if 魔導師 turns
    out to be the class, revisit `pending/chunk_043.txt`.
13. **The ch.33 sorceress is unnamed.** No name anywhere in the chunk. If a later chunk names her,
    re-check her register.
14. **`キャビア` — Cavia or Caviar?** The kana are exactly the loanword for caviar, so the pun may
    be deliberate; but the game treats it as an ordinary royal name and the fish-roe reading is
    unusable in English. Rendered *Cavia*. Revisit only if a chunk plays on the food.
15. **`ナコール` — Nacol, Nakor or Nacoll?** No in-game romanisation found. *Nacol* chosen for width
    (5 columns, fits `Ｌａｄｙ　Ｃａｖｉａ`-length lines beside it).
16. **`ティータ` is a hapax.** One occurrence in `battle_dump.txt`, none in `script_dump.txt`.
    Not a typo for ティミー: in ch.5 line 10 Fei is *surprised* by Timmy's arrival, so she cannot
    have been calling her in line 1. Plausibly Fei's beast, since Fei is a 獣使い, or a cut
    character. Rendered *Tita* pending an in-game look.
17. **`オーク` capitalisation.** Resolved to lowercase *orc* for prose (§14.3), but the class-name
    table (§10.2) may need `Ｏｒｃ`. Settle both at once.
