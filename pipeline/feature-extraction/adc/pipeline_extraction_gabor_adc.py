"""
This pipeline is intended to extract Haralick features from ADC images.
"""

import os

import numpy as np

from protoclass.data_management import ADCModality
from protoclass.data_management import GTModality

from protoclass.preprocessing import PiecewiseLinearNormalization

from protoclass.extraction import GaborBankExtraction

# Define the path where all the patients are
path_patients = '/data/prostate/experiments'
# Define the path of the modality to normalize
path_adc = 'ADC_reg_bspline'
# Define the path of the ground for the prostate
path_gt = 'GT_inv/prostate'
# Define the label of the ground-truth which will be provided
label_gt = ['prostate']
# Define the path where the information for the piecewise-linear normalization
path_piecewise = '/data/prostate/pre-processing/mp-mri-prostate/piecewise-linear-adc'
# Define the path to store the Tofts data
path_store = '/data/prostate/extraction/mp-mri-prostate/gabor-adc'

# Generate the different path to be later treated
path_patients_list_adc = []
path_patients_list_gt = []
# Create the generator
id_patient_list = [name for name in os.listdir(path_patients)
                   if os.path.isdir(os.path.join(path_patients, name))]
for id_patient in id_patient_list:
    # Append for the ADC data
    path_patients_list_adc.append(os.path.join(path_patients, id_patient,
                                               path_adc))
    # Append for the GT data - Note that we need a list of gt path
    path_patients_list_gt.append([os.path.join(path_patients, id_patient,
                                               path_gt)])

# List where to store the different minimum
for id_p, (p_adc, p_gt) in enumerate(zip(path_patients_list_adc,
                                         path_patients_list_gt)):

    print 'Processing {}'.format(id_patient_list[id_p])

    # Remove a part of the string to have only the id
    nb_patient = id_patient_list[id_p].replace('Patient ', '')

    # Read the image data
    adc_mod = ADCModality()
    adc_mod.read_data_from_path(p_adc)

    # Read the GT
    gt_mod = GTModality()
    gt_mod.read_data_from_path(label_gt, p_gt)

    # Read the normalization information
    pat_chg = id_patient_list[id_p].lower().replace(' ', '_') + '_norm.p'
    filename = os.path.join(path_piecewise, pat_chg)
    adc_norm = PiecewiseLinearNormalization.load_from_pickles(filename)

    # Normalize the data
    adc_mod = adc_norm.normalize(adc_mod)

    # Create the different parameters for the filter bank
    frequencies = np.linspace(0.05, 0.25, num=4, endpoint=True)
    alphas = np.linspace(0., np.pi, num=3, endpoint=True)
    betas = np.linspace(0., np.pi, num=3, endpoint=True)
    gammas = np.linspace(0., 2. * np.pi, num=6, endpoint=True)
    # We have less resolution in z
    scale_sigmas = np.array([1., 1., 2.])
    # Create the Gabor extractor
    gab_ext = GaborBankExtraction(adc_mod, frequencies=frequencies,
                                  alphas=alphas, betas=betas, gammas=gammas,
                                  scale_sigmas=scale_sigmas)

    # Fit the data
    print 'Compute the response for the Gabor filter bank'
    gab_ext.fit(adc_mod, ground_truth=gt_mod, cat=label_gt[0])

    # Extract the data
    print 'Extract the only the necessary pixel'
    data = gab_ext.transform(adc_mod, ground_truth=gt_mod, cat=label_gt[0])

    # Store the data
    print 'Store the data in the right directory'

    # Check that the path is existing
    if not os.path.exists(path_store):
        os.makedirs(path_store)
    pat_chg = (id_patient_list[id_p].lower().replace(' ', '_') +
               '_gabor_adc.npy')
    filename = os.path.join(path_store, pat_chg)
    np.save(filename, data)
