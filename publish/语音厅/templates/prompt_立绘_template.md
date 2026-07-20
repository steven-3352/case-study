# 语音厅立绘出图 prompt 模板 · GPT-image-2 首选

## 用法

每位演唱者出 1-2 张立绘时 · 复制对应玩法的骨架 · 填空(角色人设 · 服装 · 道具 · 场景基调) · 走 pipeline/p002 或直调 GPT-image-2 API。

**agent 应挂载 skill**([feedback_agent-auto-mount-skills](feedback_agent-auto-mount-skills) 自动):
- `[[higgsfield-character-design]]`(角色设定)
- `[[higgsfield-soul]]`(一致性 · 同角色跨镜必须同发型/服装/配饰)
- `[[higgsfield-style]]`(视觉风格)
- `[[video-form-cartoon]]` 或 `[[video-form-anime-action]]`(视觉语汇)

---

## 骨架 · 玩法 A(流行合唱 · 精修帅哥立绘)

```
Anime-style character portrait, [男/女] [年龄 18-25] singer,
[服装:详细 · 现代都市 · 如 pink argyle vest + white shirt + black tie / 
黑色皮衣 + 银链 + 白衬衫内搭 / 米色风衣 + 铃兰花束],
[发型:详细 · 如 pink beret + black side-parted hair / 红色短发狼尾 / 银白色中长发披肩],
[表情:酷酷/微笑/微冷淡 · 与人设一致],
[道具:如 麦克风/戒指/耳机/花束/唱片],
full body standing pose, contrapposto,
plain white or subtle gradient background (independent character sheet for compositing),
9:16 vertical composition,
detailed line art, cel-shading, sharp anime illustration, high quality,
--negatives: no photorealistic skin, no plastic 3D, no neon purple #bd93f9,
no neon pink #ff79c6, no neon cyan #8be9fd, no dark developer-tool canvas,
no AI slop, no extra fingers, no face morphing.
```

## 骨架 · 玩法 B(抒情陪伴 · 情感道具立绘)

```
Anime-style soft-tone character portrait, [男/女] singer with gentle expression,
[服装:轻质 · 米色/淡蓝/白 · 如 beige coat + light blue shirt + white pants /
海军蓝毛衣 + 米色长裤 · 手织感],
[道具:强化陪伴感 · 花束 / 信封 / 咖啡杯 / 手写笔记本 / 小狐狸/小猫玩偶 / 薯条挂件],
[表情:温柔微笑 / 若有所思 / 眼含泪光],
full body standing pose,
[背景基调:天蓝云海 / 爱琴海白墙 / 灯塔 / 樱花树 · 抠图后可换],
9:16 vertical composition,
detailed line art, watercolor-touch cel-shading, gentle anime illustration,
--negatives: no dark colors dominant, no aggressive contrast, no neon,
no cold blue tint on skin (feedback_no-exaggerated-cold-atmosphere),
no plastic 3D, no extra fingers, no face morphing.
```

## 骨架 · 玩法 C(国风情歌 · 冷寂帅哥立绘)

```
Anime-style Chinese guofeng character portrait, [男/女] singer,
[服装:现代改良汉服 or 中国风休闲 · 如 red qipao vest + white shirt / 
灰蓝立领长衫 + 黑色长裤 / 白色毛衣 + 深色阔腿裤 + 玉佩],
[道具:古典或诗意 · 如 white fox on shoulder / 罗马数字怀表链 / 
中式书本 / 白狐狸 / 红丝带 / 折扇 / 古琴],
[表情:淡漠 / 疏离 / 沉思 / 微忧郁],
full body standing pose,
[背景基调:罗马数字时钟盘 / 星空 / 城市剪影逆光 / 相框边饰],
9:16 vertical composition,
detailed line art, ink-wash-touch cel-shading, calligraphy-integrated,
color palette: cool gray + ink black + subtle gold accents,
--negatives: no neon, no bright saturation, no cartoonish smile,
no plastic 3D, no extra fingers, no face morphing.
```

## 骨架 · 玩法 D(嘻哈接唱 · Q 版反差萌)

**说明:** 玩法 D 主体是 **Q 版可爱形象**(不是精修帅哥) · 反差萌是灵魂。

```
Anime chibi-style character, [男/女] singer in cute proportions (SD 2.5 head-body ratio),
[服装:嘻哈街头 · 但可爱化 · 如 green army jacket + camo pants + white sneakers /
oversized hoodie + backwards cap + gold chain (mini scale) /
red bomber jacket + graffiti tee + black joggers],
[表情:超萌 · 举手挥动 / 大眼睛 / 张嘴唱到位 · 与"怒音 rap"形成反差],
chibi Q-version full body, dynamic pose (jumping / mic-hold / point-up),
[背景基调:纯白或血红舞台聚光 · 抠图后可换],
9:16 vertical composition,
detailed line art, bright cel-shading, chibi anime illustration,
color palette: allow red #e53935 + black + white (project rule allowed strong colors),
--negatives: no realistic proportions, no aggressive dark canvas without stage elements,
no neon purple/cyan (feedback_no-neon-palette),
no plastic 3D, no extra fingers, no face morphing.
```

---

## 一致性锚点(每人必录)

出图后每人在 `characters.yaml` 记录以下 anchor · 后续所有该角色 prompt 必须复用:

```yaml
- id: char_01
  name: "徐来"
  anchor:
    hair: "black side-parted medium-short hair"
    face: "oval face, warm brown eyes, small beauty mark under left eye"
    outfit: "beige trench coat, white shirt, small holding bouquet of bells-of-Ireland"
    accessory: "silver ring on left hand"
    palette: "warm beige and soft green"
    forbidden: "no other coat colors, no long hair variants"
```

**违反后果:** 跨镜换脸 = [i2v-video-diagnose](i2v-video-diagnose) §一 taxonomy 第 2 类"角色崩" · 3 次救不活升级换实现(如放弃 AI 立绘走真实素材)。

---

## Prompt 触发骨架整合(agent 用)

用户说"给我出一个 [人设描述] 的立绘 · 玩法 [A/B/C/D]" 时:
1. 挂 `higgsfield-character-design` + `higgsfield-soul` + 对应玩法子 skill
2. 从上表 4 骨架里选 · 填空
3. 走 GPT-image-2(现役 image 模型 · 项目 pipeline 已接)· 见 `pipeline/gen_scene_frames.py` 类
4. 若同角色第 2 张起 · 强制引用 anchor
5. 出图后逐帧 QA(反 AI 味 / 蓝紫 palette / 一致性)· gate fail 走 [i2v-video-diagnose](i2v-video-diagnose)
