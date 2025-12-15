## 目标概述

* 新增命令 `斗法 [@对手|道号]`：发起与目标的切磋比试，不会死亡，但会消耗修为、可能掉落物品，并存在特殊随机事件。

* 规则符合你的要求：

  * 每日可主动发起 3 次；接受挑战次数不限

  * 同一两人对战后默认 6 小时冷却（两人互相冷却）

  * 胜负基于用户表 `users.power` 判定（高者胜；相等时随机）

  * 胜者获得败者少量修为（随修为差距浮动，封顶 10%）

  * 3% 几率领悟对方一门神通（从对方已掌握的能力池随机）

  * 败者惩罚：心境稳固 `realm_stability` 降低 30%

  * 5% 几率随机掉落储物袋 1 件物品（随机一种、数量 1，掉落转移给胜者）

  * 概率触发【随机事件】并执行奖惩（事件以可配置 JSON 描述，走现有事件效果执行）

## 系统配置（system\_config）

* 新增键，全部可在后台「系统设置」编辑：

  * `duel.daily_active_limit`: int，默认 `3`（每日主动发起上限）

  * `duel.cooldown_hours_between_pair`: int，默认 `6`（两人之间冷却）

  * `duel.respect_peace_mode`: bool，默认 `true`（若目标处于【避世】则禁止被挑战）

  * `duel.power_resolution`: string，默认 `higher_wins`（`ratio` 可选：按战力占比随机）

  * `duel.xp_transfer_max_percent`: int，默认 `10`（胜者可获败者修为的最高百分比上限）

  * `duel.xp_transfer_base_percent`: int，默认 `2`（基础转移比例）

  * `duel.xp_transfer_scale`: float，默认 `0.5`（随双方修为差距的比例系数）

  * `duel.learn_ability_chance_percent`: int，默认 `3`（领悟对方神通的概率）

  * `duel.item_drop_chance_percent`: int，默认 `5`（败者随机掉落物品的概率）

  * `duel.special_event_chance_percent`: int，默认 `10`（斗法后随机事件触发概率）

  * `duel.random_events`: JSON 列表，描述可触发的随机事件（每项含 `conditions` 与 `effects`，条件支持 `probability`，效果使用现有效果 `attribute_effect`, `item_effect`, `message_effect` 等）。示例：

    ```json
    [
      {
        "name": "灵机一动",
        "conditions": [{"type": "probability", "params": {"chance": 0.3}}],
        "effects": [
          {"type": "add_xp", "params": {"value": 50, "notify": true}},
          {"type": "message", "params": {"text": "你于斗法余韵中顿悟一缕灵机。"}}
        ]
      }
    ]
    ```

  * `command_policies` 中新增：`"斗法": {"require_root": false, "allow_during": "any"}`，避免重复校验“是否踏入仙途”。（现有策略读取位置：core/database/init.py:173）

## 数据库迁移

* 新增迁移脚本（按现有 migrations 管理器追加）：

  * `0004_duel_attempts_daily`：

    * 表 `duel_attempts_daily(user_id TEXT, date TEXT, active_used INTEGER DEFAULT 0, UNIQUE(user_id, date))`

  * `0005_duel_pair_cooldowns`：

    * 表 `duel_pair_cooldowns(pair_key TEXT PRIMARY KEY, user_a TEXT, user_b TEXT, expires_at TEXT)`

    * 说明：`pair_key` 为 `(min(user_a,user_b))#(max(user_a,user_b))`，统一顺序存储

  * `0006_duel_logs`：

    * 表 `duel_logs(id INTEGER PK, challenger_id TEXT, target_id TEXT, winner_id TEXT, loser_id TEXT, xp_transferred INTEGER, item_dropped_id INTEGER, learned_ability TEXT, occurred_at TEXT DEFAULT now)`

  * 迁移流程遵循 WAL 模式与外键开启（参考 core/database/migrations.py），初始化自动应用。

## 命令与路由

* 插件主入口仅做注册（不写逻辑）：

  * 在 `main.py` 注册命令 `@filter.command("斗法")`，委托至网关（参考相同模式如“赠送” main.py:114-119）。

  * 网关新增 `async def duel(event)` 并转发至 PVP 处理器（参考 `gift_item` 入口 core/handlers/gateway.py:182-192）。

## 处理器实现（新建 PVPHandlers 或放入 social\_handlers）

* 推荐新文件 `core/handlers/pvp_handlers.py`，方法：`async def duel(event)`。

* 流程：

  * 目标解析：优先取 Reply 的原消息发送者，其次取 `@` 的 QQ/平台ID；若均无，则解析第二参数为道号并通过 `api.game.get_user_id_by_dao_name` 查询（参考用法 core/handlers/player\_handlers.py:268-270）。

  * 校验：

    * 发起方与目标方均存在档案；若配置 `respect_peace_mode=true` 且目标有 `peace_mode` 状态，则提示不可挑战（参考状态查询 core/api/player.py:926-953）。

    * 读取当日次数 `duel_attempts_daily`，若发起方已达上限则提示；写入或自增今日计数。

    * 检查两人冷却 `duel_pair_cooldowns`，若未过期则提示剩余时间。

  * 胜负判定：

    * 读取双方 `users.power` 与 `users.xp`，按 `duel.power_resolution` 执行：

      * `higher_wins`：高战力者胜；战力相等则 50% 随机

      * `ratio`：胜者概率 = `self_power / (self_power + opp_power)`

  * 修为转移：

    * 计算转移百分比 `p = min(xp_transfer_max_percent, xp_transfer_base_percent + scale*差距比率)`；

    * 实际修为 `delta = floor(loser_xp * p/100)`；胜者 `+delta`，败者 `-delta`，调用统一接口 `api.game.adjust_value(user_id, "xp", delta)`（参考 core/api/game.py:211-240）。

  * 败者惩罚：

    * `realm_stability` 减少 30%：`adjust_value(loser, "stability", -30)`（参考效果实现 core/event\_system/effects/attribute\_effect.py:216-227）。

  * 物品掉落（5%）：

    * 调用 `inventory.get_user_inventory(target)` 获取列表，随机选一种（数量>0），

    * 败者 `adjust_item_quantity(..., -1)`；胜者 `adjust_item_quantity(..., +1)`（参考 core/api/inventory.py:101-158）。

  * 神通领悟（3%）：

    * 读取对方能力池（建议以 `user_buffs` 存储 `buff_type='ability'`，`buff_name='神通:xxx'`），若存在则随机领取一项并为胜者写入同名 buff；若为空则提示本次未能领悟。

    * 能力目录建议由 `system_config.abilities_catalog` 管理，便于后台编辑与赋能。

  * 随机事件：

    * 若命中 `duel.special_event_chance_percent`，读取 `duel.random_events` 列表，按条件判断（内含 `probability` 等），逐个执行效果（直接复用现有效果类，如 `AddXpEffect`, `MessageEffect` 等）。

  * 记录日志：写入 `duel_logs` 包含胜负双方与本次结果明细。

  * 冷却登记：更新 `duel_pair_cooldowns` 的 `expires_at` 为当前+冷却小时。

  * 返回提示语（凡人修仙语境，重点信息用【】）：战报、修为得失、惩罚与事件摘要。

## 事件系统的复用

* 直接在处理器内实例化并复用效果类（与闭关实现一致，参考 core/handlers/player\_handlers.py:364-381；attribute\_effect.py）。

* 条件模块复用 `ProbabilityCondition`（core/event\_system/conditions/probability\_condition.py），用于 `duel.random_events` 的概率判断。

## 后台与前台

* 后台：无需新增控制器即可编辑上述系统配置（已支持 `system_config` 的增删改查，admin/api/system\_config.py）。

* 后台可按需新增一个简单页面/接口查看 `duel_logs`（列表查询与筛选），本次先以系统配置完成核心机制；日志查询可在下一次迭代加上。

* 前台：复用同一套 API 层（`api.game` / `api.inventory`），命令通过 `main.py` 注册到入口，业务都在处理器中进行。

## 文件改动点（位置示意）

* `main.py`：新增 `@filter.command("斗法")`，只做参数解析与网关委托（参考本文件现有命令注册 例如 114-119）。

* `core/handlers/gateway.py`：新增 `async def duel(event)`，转发到 PVPHandlers（风格同 `gift_item` 入口 182-192）。

* `core/handlers/pvp_handlers.py`：新增文件，完整实现斗法流程（解析→校验→结算→事件→日志）。

* `core/database/migrations.py`：追加 3 个迁移，创建 `duel_attempts_daily`、`duel_pair_cooldowns`、`duel_logs`。

* 无需改动现有效果与触发器；仅复用。

## 验证方式

* 启动 AstrBot 后台管理（默认端口 8888），在「系统设置」添加/编辑上述 `duel.*` 配置；为两个测试账号施行【灵根检测】并写入不同 `power/xp`。

* 在群或私聊中：

  * A 发送：`斗法 @B` 或 `斗法 B的道号`

  * 观察返回战报：

    * 胜负按战力、修为增减、败者稳固降低、可能掉落物品、可能领悟神通、可能触发随机事件

  * 重复对同一目标，确认冷却提示与每日次数限制提示按预期出现。

* 后台检查数据库：`duel_logs` 有记录；`duel_attempts_daily` 与 `duel_pair_cooldowns` 按时间更新。

## 提示

* WAL 模式保持一致；迁移与初始化阶段已设定 `PRAGMA journal_mode=WAL`（core/database/init.py），并在批量操作后适时 `PRAGMA optimize;`。计划停机前建议执行 `wal_checkpoint(TRUNCATE)`。

* 全部可配，避免硬编码；随时可在后台编辑各概率与转移比例。

## 变更摘要（用于提交信息）

* 新增命令：`斗法`（网关委托）

* 新增处理器文件：PVP 切磋流程实现（每日限 3 次、6 小时冷却、胜负按战力、修为转移≤10%、3% 领悟神通、5% 掉落物品、可配置随机事件）

* 新增数据库迁移：`duel_attempts_daily`、`duel_pair_cooldowns`、`duel_logs`

* 新增系统设置键：`duel.*` 一组与 `command_policies` 中 `斗法` 特例

