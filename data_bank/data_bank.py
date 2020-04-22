from .Data_loader_shades import Data_loader_shades
from .Data_loader_lines import Data_loader_lines
from .Data_loader_existing_lines import Data_loader_existing_lines
from .Data_loader_grad_lines import Data_loader_grad_lines
from .Data_loader_grad_shades import Data_loader_grad_shades
from .Data_loader_stripe import Data_loader_stripe_test, Data_loader_stripe_train

def data_selector(data_name, arguments):
    """ Select a data loader based on `data_name` (str).
Arguments
---------
data_name (str): Name of the data loader
arguments (dict): Dictionary given to the constructor of the data loader

Returns
-------
Data loader with name `data_name`. If not found, an error message is printed
and it returns None.
"""
    if (data_name.lower() == "shades_train") or (data_name.lower() == "shades_val") or (data_name.lower() == "shades_test"):
        return Data_loader_shades(arguments)
    elif (data_name.lower() == "lines_train") or (data_name.lower() == "lines_val") or (data_name.lower() == "lines_test"):
        return Data_loader_lines(arguments)   
    elif (data_name.lower() == "load_lines_train") or (data_name.lower() == "load_lines_val") or (data_name.lower() == "load_lines_test"):
        return Data_loader_existing_lines(arguments) 
    elif (data_name.lower() == "glines_train") or (data_name.lower() == "glines_val") or (data_name.lower() == "glines_test"):
        return Data_loader_grad_lines(arguments) 
    elif (data_name.lower() == "gshades_train") or (data_name.lower() == "gshades_val") or (data_name.lower() == "gshades_test"):
        return Data_loader_grad_shades(arguments) 
    elif (data_name.lower() == "stripe_train"):
        return Data_loader_stripe_train(arguments) 
    elif (data_name.lower() == "stripe_test") or (data_name.lower() == "stripe_val"):
        return Data_loader_stripe_test(arguments) 
    else:
        print('Error: Could not find data loader with name %s' % (data_name))
        return None;
