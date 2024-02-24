import tensorflow as tf
import numpy as np
import cv2 as cv
import os
#os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

def bn(input):
    with tf.variable_scope('bn'):
        gamma=tf.Variable(tf.random_normal(shape=[input.shape[-1].value]), name='weight',trainable=False)
        beta = tf.Variable(tf.random_normal(shape=[input.shape[-1].value]), name='bias',trainable=False)
        mean = tf.Variable(tf.random_normal(shape=[input.shape[-1].value]), name='running_mean',trainable=False)
        var = tf.Variable(tf.random_normal(shape=[input.shape[-1].value]), name='running_var',trainable=False)

        out=tf.nn.batch_normalization(input,mean,var,beta,gamma,variance_epsilon=0.001)
        return out


def conv(input,out_channels,ksize,stride,name='conv',add_bias=False):
    filter = tf.Variable(tf.random_normal(shape=[ksize, ksize, input.shape[-1].value, out_channels]),name=name+'/weight',trainable=False)

    if ksize>1:
        pad_h,pad_w=ksize//2,ksize//2
        paddings = tf.constant([[0, 0], [pad_h, pad_h], [pad_w, pad_w], [0, 0]])
        input = tf.pad(input, paddings, 'CONSTANT')
    net = tf.nn.conv2d(input, filter, [1,stride, stride, 1], padding="VALID")

    if add_bias:
        bias = tf.Variable(tf.random_normal(shape=[out_channels]),
                             name=name + '/bias',trainable=False)
        net=tf.nn.bias_add(net,bias)
    return net


def convBnLeakly(input,out_channels,ksize,stride,name,):
    with tf.variable_scope(name):
        net=conv(input,out_channels,ksize,stride)
        net=bn(net)
        #swish
        #net=tf.nn.sigmoid(net)*net
        
        #v2.0
        #net=tf.nn.leaky_relu(net,alpha=0.1)
        
        #v3.0
        net=net*tf.nn.relu6(net+3.0)/6.0
        
        return net


def focus(input,out_channels,ksize,name):
    s1=input[:,::2,::2,:]
    s2=input[:,1::2,::2,:]
    s3 = input[:, ::2, 1::2, :]
    s4 = input[:, 1::2, 1::2, :]

    net=tf.concat([s1,s2,s3,s4],axis=-1)

    net=convBnLeakly(net,out_channels,ksize,1,name+'/conv')
    return net


def bottleneck(input,c1,c2,shortcut,e,name):
    with tf.variable_scope(name):
        net=convBnLeakly(input,int(c2*e),1,1,'cv1')
        net=convBnLeakly(net,c2,3,1,'cv2')

        if (shortcut and c1==c2):
            net+=input
        return net


def bottleneckCSP(input,c1,c2,n,shortcut,e,name):
    c_=int(c2*e)
    with tf.variable_scope(name):
        net1=convBnLeakly(input,c_,1,1,'cv1')
        for i in range(n):
            net1=bottleneck(net1,c_,c_,shortcut,1.0,name='m/%d'%i)
        net1=conv(net1,c_,1,1,name='cv3')

        net2 = conv(input, c_, 1, 1, 'cv2')

        net=tf.concat((net1,net2),-1)
        net=bn(net)
        net=tf.nn.leaky_relu(net,alpha=0.1)

        net=convBnLeakly(net,c2,1,1,'cv4')
        return net


def C3(input,c1,c2,n,shortcut,e,name):
    c_=int(c2*e)
    with tf.variable_scope(name):
        net1=convBnLeakly(input,c_,1,1,'cv1')
        for i in range(n):
            net1=bottleneck(net1,c_,c_,shortcut,1.0,name='m/%d'%i)
        #net1=conv(net1,c_,1,1,name='cv3')

        net2 = convBnLeakly(input, c_, 1, 1, 'cv2')

        net=tf.concat((net1,net2),-1)
        #net=bn(net)
        #net=tf.nn.leaky_relu(net,alpha=0.1)

        net = convBnLeakly(net,2*c_,c2,1,'cv3')
        return net

def spp(input,c1,c2,k1,k2,k3,name):
    c_=c1//2
    with tf.variable_scope(name):
        net=convBnLeakly(input,c_,1,1,'cv1')

        net1=tf.nn.max_pool(net,ksize=[1,k1,k1,1],strides=[1,1,1,1],padding="SAME")
        net2=tf.nn.max_pool(net,ksize=[1,k2,k2,1],strides=[1,1,1,1],padding="SAME")
        net3 = tf.nn.max_pool(net, ksize=[1, k3, k3, 1], strides=[1, 1, 1, 1], padding="SAME")

        net=tf.concat((net,net1,net2,net3),-1)

        net=convBnLeakly(net,c2,1,1,'cv2')
        return net


def yolov5(input,class_num,model_name):
    if model_name == "m":
        depth_multiple = 0.67
        width_multiple = 0.75
    elif model_name == "l":
        depth_multiple = 1.0
        width_multiple = 1.0
    elif model_name == "x":
        depth_multiple = 1.33
        width_multiple = 1.25
    else:
        print( "model name must in  [m,l,x!]")
        return

    w1 = int(round(64 * width_multiple))
    w2 = int(round(128 * width_multiple))
    w3 = int(round(256 * width_multiple))
    w4 = int(round(512 * width_multiple))
    w5 = int(round(1024 * width_multiple))

    d1 = int(max(round(3 * depth_multiple), 1))
    d2 = int(max(round(9 * depth_multiple), 1))

    focus0=focus(input,w1,3,'model/0')
    conv1=convBnLeakly(focus0,w2,3,2,'model/1')
    bottleneck_csp2=bottleneckCSP(conv1,w2,w2,d1,True,0.5,'model/2')
    conv3 = convBnLeakly(bottleneck_csp2, w3, 3, 2, 'model/3')
    bottleneck_csp4 = bottleneckCSP(conv3, w3, w3, d2, True, 0.5, 'model/4')
    conv5 = convBnLeakly(bottleneck_csp4, w4, 3, 2, 'model/5')
    bottleneck_csp6 = bottleneckCSP(conv5, w4, w4, d2, True, 0.5, 'model/6')
    conv7 = convBnLeakly(bottleneck_csp6, w5, 3, 2, 'model/7')
    spp8=spp(conv7,w5,w5,5,9,13,'model/8')

    bottleneck_csp9 = bottleneckCSP(spp8, w5, w5, d1, False, 0.5, 'model/9')
    #head
    conv10 = convBnLeakly(bottleneck_csp9, w4, 1, 1, 'model/10')

    shape=[conv10.shape[1].value*2,conv10.shape[2].value*2]
    deconv11=tf.image.resize_images(conv10,shape,method=1)


    cat12=tf.concat((deconv11,bottleneck_csp6),-1)
    bottleneck_csp13=bottleneckCSP(cat12, w5, w4, d1, False, 0.5, 'model/13')
    conv14 = convBnLeakly(bottleneck_csp13, w3, 1, 1, 'model/14')

    shape = [conv14.shape[1].value * 2, conv14.shape[2].value * 2]
    deconv15 = tf.image.resize_images(conv14, shape,method=1)

    cat16 = tf.concat((deconv15, bottleneck_csp4), -1)
    bottleneck_csp17 = bottleneckCSP(cat16, w4, w3, d1, False, 0.5, 'model/17')
    conv18 = convBnLeakly(bottleneck_csp17, w3, 3, 2, 'model/18')

    cat19 = tf.concat((conv18, conv14), -1)
    bottleneck_csp20 = bottleneckCSP(cat19, w4, w4, d1, False, 0.5, 'model/20')
    conv21 = convBnLeakly(bottleneck_csp20, w4, 3, 2, 'model/21')

    cat22= tf.concat((conv21, conv10), -1)
    bottleneck_csp23 = bottleneckCSP(cat22, w5, w5, d1, False, 0.5, 'model/23')

    conv24m0=conv(bottleneck_csp17,3*(class_num+5),1,1,'model/24/m/0',add_bias=True)
    conv24m1 = conv(bottleneck_csp20, 3 * (class_num + 5), 1, 1, 'model/24/m/1',add_bias=True)
    conv24m2 = conv(bottleneck_csp23, 3 * (class_num + 5), 1, 1, 'model/24/m/2',add_bias=True)
    return conv24m0,conv24m1,conv24m2

def plot_one_box(img, coord, label=None, color=None, line_thickness=None):
    '''
    coord: [x_min, y_min, x_max, y_max] format coordinates.
    img: img to plot on.
    label: str. The label name.
    color: int. color index.
    line_thickness: int. rectangle line thickness.
    '''
    tl = line_thickness or int(round(0.002 * max(img.shape[0:2])))  # line thickness
    c1, c2 = (int(coord[0]), int(coord[1])), (int(coord[2]), int(coord[3]))
    # print(img.dtype,img.shape)
    # print(c1,c2)
    cv.rectangle(img, c1, c2, color)#, thickness=2
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv.getTextSize(label, 0, fontScale=float(tl) / 3, thickness=tf)[0]

        x1,y1=c1[0],c1[1]
        y1=y1 if y1>20 else y1+20
        x2,y2=x1+t_size[0],y1-t_size[1]

        cv.rectangle(img, (x1,y1), (x2,y2), color, -1)  # filled

        cv.putText(img, label, (x1, y1), 0, float(tl) / 3, [0, 0, 0], thickness=tf, lineType=cv.LINE_AA)

def post_process(inputs,grids,strides,anchor_grid,class_num):

    total=[]
    for i,logits in enumerate(inputs):
        nb=logits.shape[0]#.value
        ny = logits.shape[1]#.value
        nx = logits.shape[2]#.value
        nc = logits.shape[3]#.value

        logits=tf.reshape(logits,[nb,ny,nx,3,nc//3])
        logits=tf.sigmoid(logits)

        logits_xy=(logits[...,:2]*2.-0.5+grids[i])*strides[i]
        logits_wh = ((logits[...,2:4] * 2)**2)*anchor_grid[i]

        logits_new=tf.concat((logits_xy,logits_wh,logits[...,4:]),axis=-1)

        total.append(tf.reshape(logits_new,[-1,nc//3]))
    total=tf.concat(total,axis=0)

    mask = total[:, 4] > 0.15
    total = tf.boolean_mask(total, mask)

    #xywh--->x1y1x2y2
    x,y,w,h,conf,prob=tf.split(total,[1,1,1,1,1,class_num],axis=-1)
    x1=x-w/2
    y1=y-h/2
    x2=x1+w
    y2=y1+h
    conf_prob=conf*prob
    scores=tf.reduce_max(conf_prob,axis=-1)
    labels=tf.cast(tf.argmax(conf_prob,axis=-1),tf.float32)

    boxes=tf.concat([x1,y1,x2,y2],axis=1)
    # print(boxes,scores,labels)
    indices=tf.image.non_max_suppression(boxes,scores,max_output_size=1000,iou_threshold=0.45,score_threshold=0.25)

    boxes=tf.gather(boxes,indices)
    scores=tf.reshape(tf.gather(scores,indices),[-1,1])
    labels=tf.reshape(tf.gather(labels,indices),[-1,1])

    output=tf.concat([boxes,scores,labels],axis=-1)
    return output