from settings import *
from manifest_list import *
from preprocessor import Preprocessor
from pretrainer import *


class BatchRun():
    def __init__(self):
        pass

    def batch_processor(self, manifest_item):
        year, crop_type, start_day, end_day, sg_win, sg_poly = manifest_item
        print(crop_type)
        p = Preprocessor(year, crop_type, start_day, end_day, sg_win, sg_poly)
        p.batch_run()

    def batch_pretrain(self, process_item):
        train_years, test_year, start_day, end_day, sg_win, sg_poly = process_item
        combiner(train_years, test_year, start_day, end_day, sg_win, sg_poly,
                 MODEL_NOTE)

    def run(self, func, manifest):
        Parallel(n_jobs=2, prefer='processes', verbose=15)(
            delayed(func)(process_item)
            for process_item in manifest)


if __name__ == '__main__':
    B = BatchRun()
    if PROCESS_STATE == 0:
        print("Total file to be pre-processed: ", len(MANIFEST_PREP))  # noqa :F405
        B.run(B.batch_processor, MANIFEST_PREP)
        print("Finish processing!")
        print("Start pre-training...")
        B.run(B.batch_pretrain, MANIFEST_PRET)
        print("= = = DONE = = =")
    elif PROCESS_STATE == 1:
        print("Total file to be pre-processed: ", len(MANIFEST_PREP))  # noqa :F405
        B.run(B.batch_processor, MANIFEST_PREP)
        print("Finish processing!")
    else:
        print("Start pre-training...")
        B.run(B.batch_pretrain, MANIFEST_PRET)
        print("= = = DONE = = =")

    print("Total big jobs to be done", len(MANIFEST_PREP))  # noqa :F405
    Parallel(n_jobs=2, prefer="processes", verbose=15)(
        delayed(batch_processor)(manifest_item)
        for manifest_item in MANIFEST_PREP  # noqa :F405
    )  # let loops working in parallel
    
    Parallel(n_jobs=2, prefer='processes', verbose=15)(
        delayed(batch_pretrain)(process_item)
        for process_item in MANIFEST_PRET)
