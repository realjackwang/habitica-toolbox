## Habitica Toolbox

------

Habitica Toolbox 是一个通过调用[Habitica](https://habitica.com/)的API来实现创建定期任务的网站，在这里你可以快速的批量创建子任务，可以在任务完成后的n天自动重新创建任务。

目前只实现的和[Habitica To-Do Overs](https://github.com/Kirska/Habitica_ToDoOvers)相同的功能，后续将实现更多的功能，帮助大家更好的使用Habitica。

### Deploy

------

本项目部署在[腾讯云Serverless应用](https://console.cloud.tencent.com/sls)中，你可以直接使用，当然你可以手动部署。

#### 本地部署

`Fork`项目或者直接在`Clone`本项目

你需要2个额外的文件，cipher.bin 以及 config.py，由于这两个文件涉及数据隐私，并没有Push到GitHub。

**config.py**

你可以根据config_templates.py填写直接的config文件

**cipher.bin**

此文件是用cipher_funcitons.py生成的，首先去掉cipher_funcitons.py中的全部注释，然后用下列代码生成cipher.bin文件

```shell
python3 cipher_funcitons.py --generate
```

现在你应该可以运行此Flask项目了。

```shell
python3 app.py
```

#### 腾讯云部署

首先点击[创建Flask应用](https://console.cloud.tencent.com/sls/create?framework=flask&mode=importExistedProject&t=http)，创建一个Flask模板，并选择使用示例代码

待应用创建成功后，进入[函数服务](https://console.cloud.tencent.com/scf)，找到Flask应用对应的云函数，将`src`目录下的文件全部删除，点击编辑器的右下角，切换至终端，像本地一样，将本项目Clone至云函数的`src`目录。

```shell
git clone https://github.com/realJackWang/Habitica_ToolBox.git src
```

并和本地一样，创建 config.py 和 cipher.bin 文件。

由于腾讯云不支持在线安装依赖文件，所以你需要将所有的第三方库打包，[创建一个层](https://console.cloud.tencent.com/scf/layer-create?rid=1)，并将打包的第三方库上传，然后将这个层绑定至云函数。

此时你应该可以运行此Flask项目了。

### FAQ

------

* 为什么要做这样的一个网页
  * 我在网上看到这个[开源项目](https://github.com/Kirska/Habitica_ToDoOvers)，本来想着用他的项目直接在PythonAnywhere上部署，但是Django的部署环境，我不会配置，所以就用Flask重写一个，这样我添加新的功能也方便。
* 为什么域名这么奇怪
  * 腾讯云想要自定义域名必须先备案，暂时没有备案的打算，你也可以访问https://habitica.jackwang.cn，此链接会重定向至腾讯云的链接。

### Reference

------

* 此项目基于[Habitica To-Do Overs](https://github.com/Kirska/Habitica_ToDoOvers)开发



