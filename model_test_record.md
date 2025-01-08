| 模型 | 视频文件 | 视频时长 | 是否加入上一轮图片识别结果 | 分析结果 | 备注 |
|------|----------|----------|--------------|----------|------|
| Gemini 1.5 Pro | E14Part1.mp4 | 120s| 是 | 完全识别出来 |  |
| Gemini 1.5 Pro | E14Part2.mp4 | 120s | 是 | 完全识别出来 |  |
| Gemini 1.5 Pro | E14Part1.mp4 | 600s | 是 | 前面部分时间能完全识别，往后有较多遗漏和错误 |  |
| Gemini 1.5 Pro | E14.mp4 | 24mins | 是 | 前面部分时间识别效果还行，往后有较多遗漏和错误 |  |
| Gemini 1.5 Pro | E14Part1.mp4 | 240s | 是 | 基本准确 |  |
| Gemini 1.5 Pro | E14Part1.mp4 | 240s | 是 | 后面部分有一些遗漏 |  |
| Gemini 1.5 Pro | E14Part1.mp4 | 180s | 是 | 非常准确 |  |
| Gemini 1.5 Pro | E14Part2.mp4 | 180s | 是 | 非常准确 |  |
| Gemini 1.5 Pro | E14Part3.mp4 | 180s | 是 | 非常准确 |  |
| Gemini 1.5 Pro | E14Part1.mp4 | 180s | 是 | 效果不行 |  |
| Gemini 1.5 Pro | E14Part1.mp4 | 180s | 图和视频和prompt放在一条一起发 | 效果不行 |  |
| Gemini 1.5 Flash | E14Part1.mp4 | 180s | 是 | 基本准确 | 速度非常快，比pro快了近2/3 |
| Gemini 1.5 Flash | E14Part2.mp4 | 180s | 是 | 比较准确，后面少了一小段 | 感觉偏差无伤大雅 |
| Gemini 1.5 Flash | E14Part2.mp4 | 180s | 是 | 比较准确，后面一小段少了几秒 | 也是视频偏后段识别出错，可能缩短单段视频能降低出错率，可以改到单段 120s 或 150s 试试 |
| Gemini 1.5 Flash | E14Part0.mp4 | 120s | 是 | 后面少了两小段 | 看来 flash 还是比 pro 要弱一些 |
| Gemini 1.5 Flash | E14Part2.mp4 | 120s | 是 | 比较准确 | pro 对画面的描述会比 flash 详细一点 |

