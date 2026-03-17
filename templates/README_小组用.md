# 另一个readme可能需要修改，主要是项目结构部分

## 项目结构

```bash
CSIT5900Proj
│  .gitignore
│  Agent.py # 主文件，核心功能是定义 gradio 服务
│  client.py # 核心文件，定义 cilent
│  config.sh # 程序入口，在此设置配置
│  prompt.txt # cilent 的 system_prompt 作业的主要成果
│  README.md
│  README_小组用.md # 项目解释
│  requirements.txt
│
├─toolFiles
       Agent.py # 原生 demo
       API_test.py # 测试api 该文件及以下文件中的 system_prompt/system_prompt_a 均已弃用
       AutoTest.py
       AutoTest_Claude.py 
       AutoTest_GPT.py # 上三个是三种版本的自动测试，核心逻辑是手写若干样例自动填入agent_A回答，agent_B判断错误，其中gpt版本用到了两个api key 不过好像没区别。GPT版是实际设计、测试prompt的主要工具。
       AutoTest_TwoAgent.py # 思路与GPT相同，但似乎有错误
       AUTO_TRAIN.py # 一个新的想法，agent_A回答，B提问/判断，C评价B问题的价值，根据价值和B的判断结果更新存于文件中的两个prompt，但未使用过。
       test.txt # 某次测试输出，也许可以参考
```

其中核心文件是`Agent.py`, `client.py`, `config.sh`, `prompt.txt`. 其他几个文件是优化prompt过程的工具，也许可以加入，也许可以舍弃？

## 项目运行

在项目根目录执行

```shell
sh .\config.sh
```

打开输出的链接即可进入 Gradio 页面。其中 `clear` 按钮在清空页面的同时也会清空上下文历史。



## 其他

主要是过程中的一些点，也许ppt需要

- 最初遇到难以分辨“是否是作业”的问题，导致大量reject
- 规定输出格式后添加语义要求，结果较差 -> 强硬指令的后面（string的更后位置）出现的模糊指令\与强硬指令有关的相反指令 难以得到满足
- 减少例子，避免硬编码过拟合等干扰
- 然而对于模糊指令，适当的例子可以显著帮助判断
- 经验中的以上两点可以简单总结为：语义相近\语义区间窄的内容，适当添加例子可以帮助完成模糊判断（添加例子“why”可以显著帮助“追问”的判断）；语义区间宽，即使分类上联系再强，出现例子也会干扰判断（prompt中出现“7+5”会严重干扰其他模糊判断问题对“1+1”的判断）