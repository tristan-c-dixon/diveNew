import csv
import os
from datetime import timedelta
import fitparse


# the header fields appearing in the output csv file.  These fields are renamed versions of what appears in the
# fit field list.
header_fields = ['timestamp', 'type', 'accel_x', 'accel_y', 'accel_z', 'heart_rate', 'lat', 'lon', 'vel_x', 'vel_y',
                 'vel_z', 'dis_x', 'dis_y', 'dis_z', 'mag_x', 'mag_y', 'mag_z']


def convert_dir_fit_to_csv(input_dir, output_dir):
    """
    converts directory of .fit files to a directory of .csv flues
    :param input_dir: input directory containing .fit files
    :param output_dir: output directory where .csv files go
    """
    files = os.listdir(input_dir)
    fit_files = [file for file in files if file[-4:].lower() == '.fit']

    for file in fit_files:
        in_file = os.path.join(input_dir, file)
        out_file = os.path.join(output_dir, file[:-4] + '.csv')

        print(f'converting {in_file}')
        convert_fit_to_csv(in_file, out_file)
    print('finished conversions')


def convert_fit_to_csv(in_file, out_file):
    """
    convert .fit file to .csv file.  Note, only certain fields are processed based on the dive project.
    :param in_file: input fit file
    :param out_file: output csv file
    """
    fit_parse = fitparse.FitFile(in_file, data_processor=fitparse.StandardUnitsDataProcessor())

    save_vx = 0
    save_dx = 0
    save_vy = 0
    save_dy = 0
    save_vz = 0
    save_dz = 0

    data = []
    for m in fit_parse.messages:
        if not hasattr(m, 'fields'):
            continue

        # for debug - print out all the fields in the message - can use this to look at the all available information
        # print(m.fields)

        # turn m.fields array into a fields dictionary for ease of processing (lookup by name)
        fields = {k.name: k.value for k in m.fields}
        if 'compressed_calibrated_accel_x' in fields:
            timestamp = fields['timestamp']
            num_samples = len(fields['compressed_calibrated_accel_x'])
            vx = [0.0] * (num_samples + 1)
            dx = [0.0] * (num_samples + 1)
            vy = [0.0] * (num_samples + 1)
            dy = [0.0] * (num_samples + 1)
            vz = [0.0] * (num_samples + 1)
            dz = [0.0] * (num_samples + 1)

            vx[0] = save_vx
            dx[0] = save_dx
            vy[0] = save_vy
            dy[0] = save_dy
            vz[0] = save_vz
            dz[0] = save_dz
            dt = 1/25

            for i in range(num_samples):
                vx[i+1] = fields['compressed_calibrated_accel_x'][i] * (9.80665/1000) * dt + vx[i]
                dx[i+1] = vx[i] * dt + dx[i]
                vy[i + 1] = fields['compressed_calibrated_accel_y'][i] * (9.80665 / 1000) * dt + vy[i]
                dy[i + 1] = vy[i] * dt + dy[i]
                vz[i + 1] = fields['compressed_calibrated_accel_z'][i] * (9.80665 / 1000) * dt + vz[i]
                dz[i + 1] = vz[i] * dt + dz[i]

                # turn this row into the multiple rows dimensioned by number of samples.  The timestamp is adjusted
                # to offset by the number of samples taken within the message
                row = {'type': 'A',
                       'timestamp': timestamp - timedelta(milliseconds=((num_samples-i-1) * 1000 / num_samples)),
                       'accel_x': fields['compressed_calibrated_accel_x'][i],
                       'accel_y': fields['compressed_calibrated_accel_y'][i],
                       'accel_z': fields['compressed_calibrated_accel_z'][i],
                       'vel_x': vx[i+1],
                       'dis_x': dx[i+1],
                       'vel_y': vy[i + 1],
                       'dis_y': dy[i + 1],
                       'vel_z': vz[i + 1],
                       'dis_z': dz[i + 1],
                       }
                data.append(row)
            save_vx = vx[num_samples]
            save_dx = dx[num_samples]
            save_vy = vy[num_samples]
            save_dy = dy[num_samples]
            save_vz = vz[num_samples]
            save_dz = dz[num_samples]

        elif 'heart_rate' in fields:
            row = {'type': 'H',
                   'timestamp': fields['timestamp'],
                   'heart_rate': fields['heart_rate']}
            data.append(row)
        elif 'position_lat' in fields:
            row = {'type': 'G',
                   'timestamp': fields['timestamp'],
                   'lat': fields['position_lat'],
                   'lon': fields['position_long']}
            data.append(row)

        if 'mag_x' in fields and fields['mag_x'] is not None:
            row = {'type': 'M',
                   'timestamp':fields['timestamp'],
                   'mag_x': fields['mag_x'],
                   'mag_y': fields['mag_y'],
                   'mag_z': fields['mag_z']}
            data.append(row)

    # write out csv
    with open(out_file, 'w') as f:
        writer = csv.DictWriter(f, delimiter=',', lineterminator='\n', fieldnames=header_fields)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    convert_dir_fit_to_csv('input', 'output')
