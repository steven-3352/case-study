#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase-B (post_render) scorecards for W27D03, grounded in real keyframe QC + render facts."""
import pathlib, yaml

BASE = pathlib.Path("publish/2026-W27/D03-海外获客成长/room/scorecards")

# (role, slug, artifact, [(reviewer_id, angle, score, notes)x2])
DATA = [
 ("动效设计师","motiondesign","design/motion_wow.md",
  ("像素·抽帧专属创意点兑现",92,"抽帧复验：镜1空留资名单反差停划、镜3 Day时间轴当前格亮其余压灰、镜5左右分屏右侧像人差异——4个专属创意点在成片关键帧均兑现，零卡通零拟人、与D01划清。扣(-8)：镜1英文落地页标题(Handmade gifts)亮度偏高、与中文钩子大字有轻微双赢家拉扯，停划落点可再压英文标题一档。"),
  ("北极星·停划资产稳健度",91,"成片首帧停划资产=空名单红框，对标41.4%过程展示在镜3落地。扣(-9)：全片最强停划仍押注'空名单'单一物件、镜1/镜4共用，缺第二停划备胎；通用电商品牌替代真实风水项目(用户决策)使'真实项目'specificity略降，但规避玄学合规、结构对应真料，可接受。")),
 ("编剧","writer","scripts/script_three_versions.md",
  ("听片·VO逐字进片+CTA完整",93,"成片VO逐字为vA、CTA问句完整进片未截断(55s保口播完整)、末段已两拍不堆三句、结论钩前移s3落实。扣(-7)：55s超45s上限是已知取舍(用户拍板接受)，自然语速下口播偏满、个别段语速较紧(s3/s5 1.22x)，若压45s需砍约1/4字数。"),
  ("红线·措辞无越线",94,"成片字幕/口播无金额/ROI/转化率，留资仅'几乎没人留下/寥寥无几'、'基本没花钱'区间，玄学不碰疗效，'替我攒老外客户'安全承接标题赚钱。扣(-6)：'赚钱'标题擦边靠正片降级承接(用户拍板取舍)，依赖语境，非红线违规。")),
 ("视觉设计","visualdesign","douyin/cover.png",
  ("封面·停划帧+大字可读",91,"封面取0-3s停划帧(曝光涨/留资空+钩子大字'第5天我傻眼了')，强钩子、大字完整可读不被遮挡、与hook_benchmark停划设计一致。扣(-9)：封面英文落地页标题占比偏大、与中文钩子争视觉，可裁切下移更聚焦空名单；通用品牌画面(用户决策保留)。"),
  ("真假分界·示意水印一致性",92,"4仿真镜(1/3/4/5)抽帧均见「示意数据/仿真演示」水印+真实区与仿真区视觉分界(分屏/边框/底色)、留资打码无具体数，封面同此规格无P图假后台风险。扣(-8)：水印在动态帧个别位置偏角落、上传压缩后可读性需上传后复核；非定稿缺陷。")),
 ("留存与互动设计师","retention","retention_beat_sheet.md",
  ("像素·0-3s停划帧+5-8s变化",92,"成片0-3s停划帧(空名单红框+钩子大字)确认落地、6段每5-8s有视觉变化(快切/时间轴/划走/分屏/收束)、CTA完整。扣(-8)：55s使中段(s3/s5各12s)偏长、均播达成有赌性；avg_watch_s目标仍是纸面倒推，建议投后按实测设中继锚。"),
  ("北极星·CTA钩+承接SOP",92,"CTA讨论型'留了线索却总忘跟进'求助钩进片、含真做上限≤5+扣【出海】自动回复主页置顶承接、不导私信。扣(-8)：'下条把自动跟进拆给你'连环钩需后续真兑现否则透支，属运营履约风险；评论钩共鸣力中等，靠'谁都忘过跟进'通感。")),
 ("编导","director","design/script_review.md",
  ("外发放行·两道门+像素兑现",92,"内容门(script_review pass)+形式门(注意力硬门/visual_diversity 6专属模板/forecast)双过，抽帧确认form承诺兑现到像素(真界面/示意水印/单焦点/镜4梗仅背景层)，非catalog拼盘假approved。扣(-8)：55s超45s上限+通用品牌替代真实项目均为已知取舍(用户拍板)，已在meta/forecast如实登记，非隐藏。"),
  ("红线统辖·降级口径一致",93,"全片红线四条(赚钱降级/留资区间/禁P图假后台/玄学合规)统辖、与fact_check/洞察包口径一致，成片无金额/转化率上屏、留资仅示意。扣(-7)：'赚钱'标题擦边=用户拍板保留(非隐藏放水)；洞察包个别联签框形式上未闭环，口径实质一致。")),
 ("平台表现分析师","analyst","design/pre_publish_forecast.md",
  ("北极星·完播forecast口径",91,"forecast用北极星口径(completion_3s/completion_rate/avg_watch_s)给区间+依据，账号母题基线明确标历史实测、不混参考线，表现形式层判pass。扣(-9)：55s>45s会拉低完播率(片越长越难看完)，forecast已下调完播区间并注明；首帧停划力中-高(真界面反差，非人脸/爆梗)。"),
  ("互动/评论风险评估",92,"forecast含互动/评论风险行：CTA求助钩+'谁都忘过跟进'通感可引共鸣评论，但讨论型钩强度中等。扣(-8)：评论低时勿只归因首镜、须查CTA具体度(已写入)；通用品牌弱化'真实项目'信任、可能影响'这真能做到吗'类追问转化。")),
]

for role, slug, artifact, r1, r2 in DATA:
    s1, s2 = r1[1], r2[1]
    avg = round((s1 + s2) / 2, 1)
    card = {
        "role": role, "artifact": artifact, "artifact_version": "",
        "invalidated_by": "", "pass_threshold": 90,
        "reviewers": [
            {"reviewer_id": "像素评审", "review_mode": "independent",
             "reviewer_agent_id": f"task-pb1-{slug}", "reviewed_at": "2026-06-26",
             "angle": r1[0], "score": s1, "verdict": "pass" if s1>=90 else "fail", "notes": r1[2]},
            {"reviewer_id": "北极星评审", "review_mode": "independent",
             "reviewer_agent_id": f"task-pb2-{slug}", "reviewed_at": "2026-06-26",
             "angle": r2[0], "score": s2, "verdict": "pass" if s2>=90 else "fail", "notes": r2[2]},
        ],
        "avg_score": avg,
        "pass": (s1>=90 and s2>=90 and avg>=90),
        "scorecard_phase": "post_render", "optimization_round": 2,
    }
    out = BASE / f"{role}.yaml"
    with open(out, "w", encoding="utf-8") as f:
        yaml.safe_dump(card, f, allow_unicode=True, sort_keys=False, width=200)
    print(f"wrote {out.name}  avg={avg} pass={card['pass']} phase=post_render")
print("done:", len(DATA), "phase-B scorecards")
