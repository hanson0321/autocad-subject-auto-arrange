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

Reference paper:
https://papers.cumincad.org/data/works/att/cf2005_1_38_111.content.pdf
