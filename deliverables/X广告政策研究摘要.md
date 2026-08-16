# X广告政策研究摘要 v0.1

核验日期：2026-08-14  
范围：X官方广告政策证据与台湾／美国金融广告内部预检查  
结论边界：本文件不是法律意见，不代表X批准，也不替代台湾或美国全部法律与牌照要求。

## 已保存的X官方页面

1. [X Advertising Policies](https://business.x.com/en/help/ads-policies)
2. [Financial Products and Services](https://business.x.com/en/help/ads-policies/ads-content-policies/financial-services)
3. [Deceptive and Fraudulent Content](https://business.x.com/en/help/ads-policies/ads-content-policies/deceptive-and-fraudulent-content)
4. [Account Eligibility for X Ads](https://business.x.com/en/help/ads-policies/campaign-considerations/about-eligibility-for-x-ads)
5. [X Ads Policy Update Log](https://business.x.com/en/help/ads-policies/ads-policy-update-log)
6. [Unacceptable Content](https://business.x.com/en/help/ads-policies/ads-content-policies/unacceptable-content)

上述页面均通过 `business.x.com` 官方地址取得HTTP 200响应，并保存原始HTML、抓取时间、内容哈希、规范化摘要和追加式版本。页面没有明确提供统一的“最后更新日期”，因此 `page_updated_at` 保存为 `UNKNOWN`；不能把抓取日期当成页面更新日期。

## 与金融广告直接相关的结论

- 金融产品、金融服务以及加密和DeFi产品属于受限制类别，适用规则随产品和投放国家变化。
- 金融与加密类别要求在投放前取得X对应类别的预授权／认证；一个类别的认证不能推定覆盖另一个类别。
- 台湾金融产品与服务广告主须持有金融牌照；台湾受限制加密产品广告主同样须持有金融牌照。具体牌照类型和法律适用性仍需台湾法遵人员确认。
- X页面对美国一般金融产品仅明确列出金融聚合器可在限制条件下投放，并未列完美国全部金融法律或牌照条件。因此本框架不会自行推测美国一般金融牌照。
- 美国受限制加密产品广告主须提供SEC、CFTC或FinCEN注册证明。
- ICO、IEO、IDExO以及加密挖矿和相关软硬件服务被列为禁止推广内容。

## 内容、账号与落地页规则

- 禁止保证盈利、快速致富、固定时间获得不现实结果以及其他缺乏依据的收益承诺。
- 禁止夸张点击诱导、误导主张、虚假优惠或稀缺，以及遗漏价格、费用或付款条件。
- 禁止伪装页面、限制落地页访问、提交后修改URL以规避审核、过度跳转、无效功能或无效CTA。
- 广告账号帖子须公开，账号不得停用或暂停；企业／政府与个人账号须按X指定方式完成验证。
- Bio URL须可用、在线、非门控，并准确代表品牌和推广产品或服务。
- 不得利用敏感事件或争议议题牟利，不得暗示未经授权的平台关系、特殊权限或审核能力。

## 预检查结果解释

- `PASS_PRECHECK`：只表示本框架内部字段完整且未触发已结构化阻塞规则，不代表Guaranteed Approval。
- `REVIEW_REQUIRED`：存在需要人工核验或修正的披露、账号或政策时效问题。
- `BLOCKED`：触发明确禁止内容、明确缺少必要牌照／预授权、落地页不可访问或规避审核等规则。
- `UNKNOWN`：政策快照、产品、主体、牌照、账号或落地页事实不足，不能猜测。

当前没有提供真实广告主体、产品、牌照、X预授权、账号验证或落地页资料，因此四份模板的当前结果均为 `UNKNOWN`。
