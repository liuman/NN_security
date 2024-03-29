"""
This file read a `config.yml` file and train a network based on the settings
in that file
"""

import yaml
import shutil
import uuid
from tensorflow.keras import backend as K
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from nn_tools import read_count
import tensorflow as tf
from data_bank import data_selector
import model_builders as mb
#from SaveWeights import MyCallback
from validation import Validation_Callback, Sparse_Validation_Callback
import os
from os.path import join
import matplotlib.pyplot as plt;
import numpy as np;
import sys
from tensorflow.keras.applications.resnet50 import preprocess_input as res_prep
from tensorflow.keras.applications.vgg16 import preprocess_input as vgg_prep
import gc
from tensorflow.keras.losses import SparseCategoricalCrossentropy
from tensorflow.keras.metrics import SparseCategoricalAccuracy



if __name__ == "__main__":
    """Train a full model based on the settings in `config.yml`"""
    # Turn off unnessesary warnings
    tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
    
    # Load configuration file
    configfile = 'config_files/config_continue.yml'
    with open(configfile) as ymlfile:
        cgf = yaml.load(ymlfile, Loader=yaml.SafeLoader);

    # Set up computational resource 
    use_gpu = cgf['COMPUTER_SETUP']['use_gpu']
    print("""\nCOMPUTER SETUP
Use gpu: {}""".format(use_gpu))
    if use_gpu:
        compute_node = cgf['COMPUTER_SETUP']['compute_node']
        os.environ["CUDA_VISIBLE_DEVICES"]= "%d" % (compute_node)
        print('Compute node: {}'.format(compute_node))
    else: 
        os.environ["CUDA_VISIBLE_DEVICES"]= "-1"

    # Turn on soft memory allocation
    tf_config = tf.compat.v1.ConfigProto()
    tf_config.gpu_options.allow_growth = True
    tf_config.log_device_placement = False
    sess = tf.compat.v1.Session(config=tf_config)
    #K.v1.set_session(sess)
    
    # Load train and validatation data
    data_loader_train = data_selector(cgf['DATASET_TRAIN']['name'], cgf['DATASET_TRAIN']['arguments'])
    data_loader_validate = data_selector(cgf['DATASET_VAL']['name'], cgf['DATASET_VAL']['arguments'])
    print('\nDATASET TRAIN')
    print(data_loader_train)
    print('DATASET VALIDATION')
    print(data_loader_validate)
    
    train_data, train_labels,_ = data_loader_train.load_data();
    val_data, val_labels,_ = data_loader_validate.load_data();
    
    # Trying for resnet since memory seems to be the issue
    train_data = train_data[:3000,:,:]
    train_labels = train_labels[:3000] 


    if (cgf['MODEL']['name'] == "resnet"):
        train_data = 255*train_data
        train_data = train_data - 122
        # train_data = np.repeat(train_data,3,-1)
        val_data = 255*val_data - 122
        # val_data = np.repeat(val_data,3,-1)
        train_data = tf.cast(train_data, dtype=tf.float32)
        val_data = tf.cast(val_data, dtype=tf.float32)
        train_labels = tf.cast(train_labels, dtype=tf.float32)
        val_labels = tf.cast(val_labels, dtype=tf.float32)
        #train_data= res_prep(train_data)
        #val_data= res_prep(val_data)
    
    elif cgf['MODEL']['name'] == 'vgg16':
        train_data = 255*train_data - 122
        # train_data = np.repeat(train_data,3,-1)
        val_data = 255*val_data - 122
        # val_data = np.repeat(val_data,3,-1)
        train_data = tf.cast(train_data, dtype=tf.float32)
        val_data = tf.cast(val_data, dtype=tf.float32)
        train_labels = tf.cast(train_labels, dtype=tf.float32)
        val_labels = tf.cast(val_labels, dtype=tf.float32)
        # train_data= vgg_prep(train_data)
        # val_data= vgg_prep(val_data)
    

    # Get input and output shape
    input_shape = train_data.shape[1:]
    output_shape = train_labels.shape[1];
    print('input_shape', input_shape)
    # Set the default precision 
    model_precision = cgf['MODEL_METADATA']['precision']
    K.set_floatx(model_precision)

    # Print model information
    model_name = cgf['MODEL']['name']
    model_arguments = cgf['MODEL']['arguments']
    print("""MODEL
name: {}
arguments:""".format(model_name))
    for key, value in cgf['MODEL']['arguments'].items():
        print("\t{}: {}".format(key,value))

    # Extract training information
    loss_type = cgf['TRAIN']['loss']['type']
    optimizer = cgf['TRAIN']['optim']['type']
    batch_size = cgf['TRAIN']['batch_size']
    metric_list = list(cgf['TRAIN']['metrics'].values()) 
    shuffle_data = cgf['TRAIN']['shuffle'] 
    max_epoch = cgf['TRAIN']['max_epoch']
    stpc_type = cgf['TRAIN']['stopping_criteria']['type']
    print("""\nTRAIN
loss: {}
optimizer: {}
batch size: {}
shuffle data between epochs: {}
max epoch: {}
stopping_criteria: {}""".format(loss_type, optimizer, batch_size, shuffle_data, 
           max_epoch, stpc_type))

    # Sparse Categorical Crossentropy for adv attacks
    if loss_type == 'SparseCategoricalCrossentropy':
        loss_type = SparseCategoricalCrossentropy(from_logits=True)
        metric_list = [SparseCategoricalAccuracy()]
        output_shape = 2
        train_labels = np.reshape(train_labels, (-1))
        val_labels = np.reshape(val_labels, (-1))

    # Load model
    model = mb.model_selector(model_name, input_shape, output_shape, model_arguments)


    callbacks = None
    if stpc_type.lower() == 'epoch' or stpc_type.lower() == 'epochs':
        callbacks = None
    elif stpc_type.lower() == "earlystopping" or stpc_type.lower() == "early_stopping":
        arguments = cgf['TRAIN']['stopping_criteria']['arguments']
        es = EarlyStopping(**arguments)
        callbacks = [es]
        for key, value in arguments.items():
            print('\t{}: {}'.format(key,value))
    else:
        print('Unknown stopping criteria')
        callbacks = None
    print('')
    
    #model = tf.keras.models.load_model('model/300/best_model_resnet.h5')
    model.load_weights('model/302/best_model_resnet.h5', by_name= True, skip_mismatch=True)


    opt = tf.keras.optimizers.Adam() 
    # Compile model
    model.compile(optimizer = opt, 
                 loss = loss_type,
                 metrics = metric_list)
 
    
    # Model metadata
    save_final_model = cgf['MODEL_METADATA']['save_final_model']
    save_best_model = cgf['MODEL_METADATA']['save_best_model']['use_model_checkpoint']
    print("""MODEL METADATA
Precision: {}
Save final model: {}""".format(model_precision, save_final_model))
    if save_final_model or save_best_model: # Get a model id
        
        dest_model = cgf['MODEL_METADATA']['dest_model']
        model_number_type = cgf['MODEL_METADATA']['model_number_type']
        if model_number_type.lower() == 'fixed':
            model_number = cgf['MODEL_METADATA']['model_number_arguments']['model_id']
        elif model_number_type.lower() == 'count':
            counter_path =\
                cgf['MODEL_METADATA']['model_number_arguments']['counter_path']
            model_number = read_count(counter_path);
        elif model_number_type.lower() == 'uuid':
            model_number = uuid.uuid1().int
        else:
            model_number = -1;
        
        full_dest_model = join(dest_model, str(model_number))
        if not os.path.isdir(dest_model):
            os.mkdir(dest_model)
        if not os.path.isdir(full_dest_model):
            os.mkdir(full_dest_model)
        else:
            print('Delete all content in the folder: \n{}'.format(full_dest_model))
            shutil.rmtree(full_dest_model);
            os.mkdir(full_dest_model)
        shutil.copyfile(configfile, join(full_dest_model, 'config.yml'))
        shutil.copyfile('model_builders.py', join(full_dest_model, 'model_builders.py'))
        print("""Model nbr type: {}
Model number: {}
Model dest: {}""".format(model_number_type, model_number, dest_model))
   
    print('Save best model: {}'.format(save_best_model))
    
    ''' 
    if save_best_model:
        arguments = cgf['MODEL_METADATA']['save_best_model']['arguments']
        for key, value in arguments.items():
            print('\t{}: {}'.format(key,value))

        filename = arguments['filepath']
        arguments['filepath'] = join(full_dest_model, filename)
        mc = ModelCheckpoint(arguments['filepath'], monitor=arguments['monitor'], verbose=arguments['verbose'], save_best_only=False, save_weights_only=True, mode=arguments['mode'], period=arguments['period'])
        if callbacks is None:
            callbacks = mc
        elif type(callbacks) is list: # Is a list
            callbacks.append(mc)
        else:
            callbacks = mc
            print('ERROR: Unknown callback type')
    '''
    '''
    # We save weights after each epoch
    if callbacks == None:
        callbacks =[]
    mycallback = MyCallback()
    callbacks.append(mycallback)
    '''

    # Put valiation into callback
    if callbacks == None:
        
        validationCallback = Validation_Callback(validation_data = (val_data, val_labels), interval = 1) 
        callbacks = [validationCallback]
    else:
        
        validationCallback = Validation_Callback(validation_data = (val_data, val_labels), interval = 1) 
        callbacks.append(validationCallback)

    if cgf['TRAIN']['loss']['type'] == 'SparseCategoricalCrossentropy':
        validationCallback = Sparse_Validation_Callback(validation_data = (val_data, val_labels), interval=1)
        callbacks = [validationCallback]

    print('\nStart training the model\n')
    # Train model :)
 
    print(shuffle_data)
    print(callbacks)

    history = model.fit(train_data, train_labels, 
              epochs=max_epoch, 
              batch_size=batch_size,
              #validation_data=(val_data, val_labels),
              shuffle=shuffle_data,
              callbacks = callbacks)

    filepath = cgf['MODEL_METADATA']['save_best_model']['arguments']['filepath']

    if save_final_model:
        full_file_name = join(full_dest_model, filepath)
        model.save(join(full_dest_model, filepath), save_format='h5')
        print('Saved model as {}'.format(full_file_name))

    # plot the loss history
    '''
    plt.figure()
    loss_hist = history.history['loss'][int(max_epoch/2):]
    index = np.linspace(max_epoch/2+1, max_epoch, max_epoch/2);
    plt.plot(index,loss_hist);
    plt.savefig(join(full_dest_model, 'loss_graph.png'));
    '''

    gc.collect()
    K.clear_session()
    '''
    # Load and test model on test set
    data_loader_test = data_selector(cgf['DATASET_TEST']['name'], cgf['DATASET_TEST']['arguments'])
    print('\nDATASET TEST')
    print(data_loader_test)
    
    test_data, test_labels, _ = data_loader_test.load_data()

    if (cgf['MODEL']['name'] == "resnet") or (cgf['MODEL']['name'] == "vgg16"):
        test_data = np.repeat(test_data,3,-1)
        test_data = tf.cast(test_data, dtype=tf.float16)   
        test_labels = tf.cast(test_labels, dtype=tf.float16)
        test_data = preprocess_input(test_data) 
    score = model.evaluate(test_data, test_labels, verbose=0, batch_size=batch_size)
    print('Accuracy on test set: {}%'.format(100*score[1]))
    '''
