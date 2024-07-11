INPUT:

- 加入新物件: 在obj_params那個dictionary可以加入新物件擺放
- 指定不能擺放物件的區域: unusable_gridcell

OUTPUT:

- run layout_latestVer.py會產出一個dxf及matplotlib的擺放示意圖

Objective function:

- 目前就是設定擺得進去就可以，還沒有一個特定的objective function

可擺放範圍:

- 目前是設定為一個方正空間，尚未加入實際可行區域

Tools:

- 一些前處理的code，目前尚未和主程式嫁接

Different versions of code

看大家在做的code是哪個部分可以用不同的code去試
- layout_latetestVer.py: 單純擺放進去，沒有貨架區的maximization
- layout_shelf_maximize.py: 貨架區擺放，但沒有把全部物件都放進去
- layoput_steps.py: 分兩類擺放，靠牆的物件先擺，不靠牆的物件後擺。目前這個方式可以擺放所有物件可以跑出結果，但座位區的擺放還沒加入。

Reference paper:
https://papers.cumincad.org/data/works/att/cf2005_1_38_111.content.pdf
