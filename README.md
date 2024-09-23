INPUT:

- doc = 'dxf檔案'
- 加入新物件: 在obj_params那個dictionary可以加入新物件擺放
- 指定不能擺放物件的區域: unusable_gridcell

OUTPUT:

- run layout_heuristic.py會產出一個dxf及matplotlib的擺放示意圖

Objective:

- Group 0

  後櫃台靠牆
  
  越靠近大門越好
  
  垂直大門
  
  面向大門那側前後櫃台切齊
  
  前後櫃台間距110
  
  前櫃台預留排隊空間
  
  <img width="510" alt="image" src="https://github.com/user-attachments/assets/2f84b0eb-d037-424c-9bba-1f6dae919d04">

- Group 0.1/0.2
  
  WI、RI靠牆擺放
  
  OC、雙溫櫃及單溫櫃要和大型物件及前櫃檯切齊
  
  形成的後場作業區不能擺放物件
  
<img width="479" alt="image" src="https://github.com/user-attachments/assets/877eae78-63c9-4000-a496-84d49c098f6f">

- Group 0.5
  
  靠近門口
  
  靠近前櫃台
  
  靠牆
  
  兩個物件彼此靠近
  
  如果有畸零地盡量擺放在畸零地上
  
<img width="519" alt="image" src="https://github.com/user-attachments/assets/06fac19c-afe0-4578-a718-6caf4fc72163">

- Group 0.8
  
  靠牆
  
  離門口越遠越好
  
<img width="494" alt="image" src="https://github.com/user-attachments/assets/3838ebbf-0570-4f96-a0bc-9bb70ecf0f7b">

- Group 1

  靠牆
  
<img width="464" alt="image" src="https://github.com/user-attachments/assets/df381b75-e3f5-498a-8f32-ae3438d39003">

- Gruop 2
  
  貨架數量要在25~35之間，並且越多越好
  
  貨架擺放垂直櫃台，並且越靠近越好
  
  貨架擺放靠櫃台的面要切齊
  
  貨架之間保持走道間距
  
  優先選擇貨架數量為9或11個的貨架規格
  
  FF（熟食區）加入貨架區擺放
  
  FF越靠近櫃台越好
  
<img width="590" alt="image" src="https://github.com/user-attachments/assets/54451f04-a9c1-4ccc-ace4-10f7c39ff10c">

Tools:
- 一些前處理的code
- 可擺放範圍:
  
  get_feasible_area.py: 抓出可行解範圍，並且抓出門的位置，大門位置


Reference paper:
https://papers.cumincad.org/data/works/att/cf2005_1_38_111.content.pdf
