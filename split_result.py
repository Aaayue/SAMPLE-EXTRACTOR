import numpy as np
import os

def save_to_npz(dataset, out_path, yr, ctype):
        """
          function to save to npz file
          chunk data into small pieces
          """
        if not out_path.startswith(os.path.expanduser("~")):
            out_path = os.path.join(os.path.expanduser("~"), out_path.strip("./"))

        length = len(dataset)
        print(length)
        chunk = 10000  # arbitrary chunk size
        iter_total = int(length / chunk) + 1
        print(iter_total)
        for n in range(iter_total):
            # tmp = itertools.islice(dataset.items(), n * chunk, (n + 1) * chunk)
            tmp = list(dataset)[(n*chunk):(n + 1)*chunk]  # noqa : E203
            try:
                os.remove(
                    os.path.join(
                        out_path,
                        yr
                        + "_"
                        + ctype
                        + "_"
                        + "extractor_results"
                        + "_"
                        + str(n)
                        + ".npz",
                    )
                )
            except Exception:
                pass

            np.savez(
                os.path.join(
                    out_path,
                    yr
                    + "_"
                    + ctype
                    + "_"
                    + "extracted_results"
                    + "_"
                    + str(n)
                    + ".npz",
                ),
                tmp,
            )
            print('finish' + str(n))

if __name__ == "__main__":
    file = '/home/zy/data_pool/U-TMP/excersize/point_extractor/extract_points/North_XJ/2018_OtherCrop_extracted_results.npz'
    yr = '2018'
    cty = os.path.split(file)[1].split('_')[1]
    out = os.path.split(file)[0]
    data = np.load(file)['arr_0']
    save_to_npz(data, out, yr, cty)
    
