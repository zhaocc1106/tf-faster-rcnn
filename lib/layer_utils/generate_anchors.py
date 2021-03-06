# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Faster R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick and Sean Bell
# --------------------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np


# Verify that we compute the same anchors as Shaoqing's matlab implementation:
#
#    >> load output/rpn_cachedir/faster_rcnn_VOC2007_ZF_stage1_rpn/anchors.mat
#    >> anchors
#
#    anchors =
#
#       -83   -39   100    56
#      -175   -87   192   104
#      -359  -183   376   200
#       -55   -55    72    72
#      -119  -119   136   136
#      -247  -247   264   264
#       -35   -79    52    96
#       -79  -167    96   184
#      -167  -343   184   360

# array([[ -83.,  -39.,  100.,   56.],
#       [-175.,  -87.,  192.,  104.],
#       [-359., -183.,  376.,  200.],
#       [ -55.,  -55.,   72.,   72.],
#       [-119., -119.,  136.,  136.],
#       [-247., -247.,  264.,  264.],
#       [ -35.,  -79.,   52.,   96.],
#       [ -79., -167.,   96.,  184.],
#       [-167., -343.,  184.,  360.]])

def generate_anchors(base_size=16, ratios=[0.5, 1, 2],
                     scales=2 ** np.arange(3, 6)):
  """
  Generate anchor (reference) windows by enumerating aspect ratios X
  scales wrt a reference (0, 0, 15, 15) window.
  注意，这里生成的是原始图片中anchors，并不是feature map中的。这里假设原始图片中基本anchor是16 × 16的尺寸。
  """

  base_anchor = np.array([1, 1, base_size, base_size]) - 1
  """
  生成不同纵横比（ratios）所对应的矩形，用左上角和右下角坐标来描述矩形，前两个值为左上角的
  xy坐标，后两个值为右下角的xy坐标。
  比如输入的矩形为(0, 0) - (15, 15)，输出的anchors如下：
  array([[-3.5,  2. , 18.5, 13. ],    0.5纵横比
         [ 0. ,  0. , 15. , 15. ],    1.0纵横比
         [ 2.5, -3. , 12.5, 18. ]])   2.0纵横比
  """
  ratio_anchors = _ratio_enum(base_anchor, ratios)

  """
  为上述生成的所有纵横比的anchors矩形，生成不同扩大比例（scales）对应的anchors矩形。用左上
  角和右下角坐标来描述矩形，前两个值为左上角的xy坐标，后两个值为右下角的xy坐标。
  比如输入：
  array([[-3.5,  2. , 18.5, 13. ],    0.5纵横比
         [ 0. ,  0. , 15. , 15. ],    1.0纵横比
         [ 2.5, -3. , 12.5, 18. ]])   2.0纵横比
  输出为：
  array([[ -84.,  -40.,   99.,   55.],    0.5纵横比，8倍扩大
         [-176.,  -88.,  191.,  103.],    0.5纵横比，16倍扩大
         [-360., -184.,  375.,  199.],    0.5纵横比，32倍扩大
         [ -56.,  -56.,   71.,   71.],    1.0纵横比，8倍扩大
         [-120., -120.,  135.,  135.],    1.0纵横比，16倍扩大
         [-248., -248.,  263.,  263.],    1.0纵横比，32倍扩大
         [ -36.,  -80.,   51.,   95.],    2.0纵横比，8倍扩大
         [ -80., -168.,   95.,  183.],    2.0纵横比，16倍扩大
         [-168., -344.,  183.,  359.]])   2.0纵横比，32倍扩大
  """
  anchors = np.vstack([_scale_enum(ratio_anchors[i, :], scales)
                       for i in range(ratio_anchors.shape[0])])
  return anchors


def _whctrs(anchor):
  """
  Return width, height, x center, and y center for an anchor (window).
  """
  # 根据矩形的左上角和右下角坐标
  # 计算矩形的宽高
  w = anchor[2] - anchor[0] + 1
  h = anchor[3] - anchor[1] + 1
  # 计算矩形的中心点坐标
  x_ctr = anchor[0] + 0.5 * (w - 1)
  y_ctr = anchor[1] + 0.5 * (h - 1)
  return w, h, x_ctr, y_ctr


def _mkanchors(ws, hs, x_ctr, y_ctr):
  """
  Given a vector of widths (ws) and heights (hs) around a center
  (x_ctr, y_ctr), output a set of anchors (windows).
  """

  # 根据矩形的宽高获取矩形的左上角和右下角坐标
  ws = ws[:, np.newaxis]
  hs = hs[:, np.newaxis]
  anchors = np.hstack((x_ctr - 0.5 * (ws - 1),
                       y_ctr - 0.5 * (hs - 1),
                       x_ctr + 0.5 * (ws - 1),
                       y_ctr + 0.5 * (hs - 1)))
  return anchors


def _ratio_enum(anchor, ratios):
  """
  Enumerate a set of anchors for each aspect ratio wrt an anchor.
  """

  # 获取矩形的宽高和中心点坐标
  w, h, x_ctr, y_ctr = _whctrs(anchor)
  size = w * h

  """
  纵横比ratios不造成面积的变化，所以三种纵横比的长宽计算方式如下：
  0.5纵横比： w * (0.5 * w) = size
  1纵横比: w * (1 * w) = size
  2纵横比: w * (2 * w) = size
  ws和hs就是算出来的不同纵横比的长宽。
  """
  size_ratios = size / ratios
  ws = np.round(np.sqrt(size_ratios))
  hs = np.round(ws * ratios)

  # 获取不同纵横比情况下矩形的左上角坐标和右下角坐标
  anchors = _mkanchors(ws, hs, x_ctr, y_ctr)
  return anchors


def _scale_enum(anchor, scales):
  """
  Enumerate a set of anchors for each scale wrt an anchor.
  """

  # 获取矩形的中心点坐标和宽高
  w, h, x_ctr, y_ctr = _whctrs(anchor)

  # 宽高各自乘上scales扩大的倍数
  ws = w * scales
  hs = h * scales

  # 根据现在的中心点坐标和宽高获取矩形左上角和右下角的坐标，就实现了矩形的放大
  anchors = _mkanchors(ws, hs, x_ctr, y_ctr)
  return anchors


if __name__ == '__main__':
  import time

  t = time.time()
  a = generate_anchors()
  print(time.time() - t)
  print(a)
  from IPython import embed;

  embed()
