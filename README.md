# invoice-box

这个项目是为了处理日常加班票据的提取,解决每次要打开电子票据或者图片,然后重新命名文件命.
目前支持滴滴出行,美团,饿了么外卖信息提取.

# 如何使用
需要将你的票据发送到邮箱[einvoice@sina.com](einvoice@sina.com),然后主题命名为你想要的文件名格式
比如Wes-{money}-{date:%m%d}
目前支持暂时数据变量只有两种
1. money 票据金额
2. date 票据日期(支持的格式月日:%m%d,年月日:%Y%m%d)
滴滴的处理需要把滴滴完整的邮件当成附件添加到邮件中,图片或者pdf直接添加为附件.可以参考以下的gif图操作.

![](https://cdn.jsdelivr.net/gh/wes-lin/invoice-box/imgs/send.gif)

# 处理时间
因为是github action 的定时触发,一天只执行三次分别是8:00,12:00,16:00,请在处理时间点发送你的票据这样才能有效处理到.

# 处理结果
任务处理完毕后,会将原始的单据重名成你的格式,然后按原始邮箱给你发送回去.

![](https://cdn.jsdelivr.net/gh/wes-lin/invoice-box/imgs/respose.png)