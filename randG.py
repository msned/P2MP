import os
desired_size = 1024*50
desired_number_of_files = 1
for file_number in range(desired_number_of_files):
    filename = 'demoData.dat'
    with open(filename, 'wb') as fout: fout.write(os.urandom(desired_size))
print('Done.')