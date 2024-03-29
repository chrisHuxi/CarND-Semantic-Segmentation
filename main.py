#!/usr/bin/env python3
import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests


# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights
    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'
    
    meta_graph_def  = tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)
    
    image_input = sess.graph.get_tensor_by_name(vgg_input_tensor_name)
    print(tf.shape(image_input))
    keep_prob = sess.graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    print(tf.shape(keep_prob))
    layer3_out = sess.graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    print(tf.shape(layer3_out))
    layer4_out = sess.graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    print(tf.shape(layer4_out))
    layer7_out = sess.graph.get_tensor_by_name(vgg_layer7_out_tensor_name)
    print(tf.shape(layer7_out))
    return image_input, keep_prob, layer3_out, layer4_out, layer7_out
    #TODO END
    
tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer3_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer7_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function
    # note: encoder part already done by vgg, we only need to implement decoder
    # architecture: https://www.researchgate.net/figure/Fully-convolutional-neural-network-architecture-FCN-8_fig1_327521314
    conv_1x1 = tf.layers.conv2d(vgg_layer7_out, num_classes, 1, strides=(1,1),padding = "same",
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(scale=0.001))
    #change depth to num_classes by applying 1x1 conv
    
    decoder_out1 = tf.layers.conv2d_transpose(conv_1x1, num_classes, 4, strides=(2, 2), padding = "same",
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(scale=0.001))
    #don't know why filter size = 4, strides = (2,2)                         
    
    vgg_layer4_out_scaled = tf.multiply(vgg_layer4_out, 0.01)
    conv_1x1_skip1 = tf.layers.conv2d(vgg_layer4_out_scaled, num_classes, 1, strides=(1,1),padding = "same",
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(scale=0.001))
                                
    skip_connection1 = tf.add(decoder_out1, conv_1x1_skip1)
    
    #skip connection
    
    decoder_out2 = tf.layers.conv2d_transpose(skip_connection1, num_classes, 4, strides=(2, 2), padding = "same",
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(scale=0.001))
    
    vgg_layer3_out_scaled =  tf.multiply(vgg_layer3_out, 0.0001)
    conv_1x1_skip2 = tf.layers.conv2d(vgg_layer3_out, num_classes, 1, strides=(1,1),padding = "same",
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(scale=0.001))
     
    skip_connection2 = tf.add(decoder_out2, conv_1x1_skip2)
    
    decoder_out = tf.layers.conv2d_transpose(skip_connection2, num_classes, 16, strides=(8, 8), padding = "same",
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(scale=0.001))
    return decoder_out
    # TODO END
    
tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    logits = tf.reshape(nn_last_layer, (-1, num_classes))
    correct_label_reshape = tf.reshape(correct_label, (-1, num_classes))
    l2_loss = tf.losses.get_regularization_loss()
    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels = correct_label_reshape[:],logits = logits))
    cross_entropy_loss += l2_loss
    train_op = tf.train.AdamOptimizer(learning_rate).minimize(cross_entropy_loss)
    # TODO: Implement function
    return logits, train_op, cross_entropy_loss
    # TODO: END
tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function
    # Add the ops to initialize variables.  These will include 
    # the optimizer slots added by AdamOptimizer().
    learning_rate_para = 0.000001
    keep_prob_para = 0.6
    init_op = tf.global_variables_initializer()
    sess.run(init_op)
    sum_loss = 0.0
    for epoch in range(1,epochs+1):
        for x,y in get_batches_fn(batch_size): #这里有疑问：能不能用batch?
            loss, _ = sess.run([cross_entropy_loss,train_op],feed_dict = {input_image:x, correct_label:y, learning_rate:learning_rate_para, keep_prob:keep_prob_para})
            sum_loss += loss
        if epoch % 1 == 0:
            #loss = sess.run(cross_entropy_loss, feed_dict = {input_image:x, correct_label:y, learning_rate: 0.1, keep_prob:0.6})
            print("Epoch {:03d}: Loss: {:.3f}".format(epoch,sum_loss))
            sum_loss = 0.0
    # TODO: END
tests.test_train_nn(train_nn)


def run():
    num_classes = 2
    image_shape = (160, 576)  # KITTI dataset uses 160x576 images
    data_dir = '/data'
    runs_dir = '/runs'
    tests.test_for_kitti_dataset(data_dir)

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    #=============== tune parameter here ==============#
    epochs = 40
    batch_size = 32
    
    #=============== tune parameter here ==============#
       
    correct_label = tf.placeholder(tf.float32, [None, None, None, num_classes])
    learning_rate = tf.placeholder(tf.float32, name='learning_rate')
    
    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        image_input, keep_prob, layer3_out, layer4_out, layer7_out = load_vgg(sess,vgg_path)
        nn_last_layer = layers(layer3_out, layer4_out, layer7_out, num_classes)
        
        logits, train_op, cross_entropy_loss = optimize(nn_last_layer, correct_label, learning_rate, num_classes)

        # TODO: Train NN using the train_nn function
        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, image_input,
             correct_label, keep_prob, learning_rate)
        # TODO: Save inference data using helper.save_inference_samples
        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        # OPTIONAL: Apply the trained model to a video


if __name__ == '__main__':
    run()
