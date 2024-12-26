from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from chardet.universaldetector import UniversalDetector
from chardet import detect


def detect_encoding_old(filepath: Path, n_lines=10) -> str | None:
    filepath = Path(filepath).absolute()

    with open(filepath, "rb") as f:
        rawdata = b''.join([f.readline() for _ in range(n_lines)])

    return detect(rawdata)['encoding']


def detect_encoding(filepath: Path):
    filepath = Path(filepath).absolute()
    with open(filepath, 'rb') as file:
        detector = UniversalDetector()
        for line in file:
            detector.feed(line)
            if detector.done:
                detector.close()
                break
        else:
            detector.close()
            return None
            raise IOError(
                f"Could not determine encoding of file {filepath.name}")
    return detector.result['encoding']


def sanitize_mail(filepath: Path, output_path=None):
    filepath = Path(filepath).absolute()
    if output_path is None:
        output_path = filepath
    else:
        output_path = Path(output_path).absolute()
    try:
        encoding = detect_encoding(filepath)

        with open(filepath, "r", encoding=encoding) as f:
            try:
                content = f.read()
            except UnicodeDecodeError as e:
                raise IOError(
                    f"File {filepath} could not be read") from e
        output_content = [line for line in content.splitlines(
        ) if not line.startswith("X-Mozilla-")]

        with open(output_path, "w", encoding=encoding) as f:
            f.write("\n".join(output_content))
    except IOError as e:
        return e
    return None


def sanitize():

    parser = ArgumentParser()
    parser.add_argument(
        "-f", "--folder", help="Folder to sanitize", default=None)
    parser.add_argument(
        "-c", "--cpus", help="Number of CPUS to use", default=cpu_count(), type=int, required=False)

    args = parser.parse_args()

    if args.folder:
        input_folder = Path(args.folder).absolute()

        files_to_process = [
            file for file in input_folder.iterdir() if file.is_file()]
        nb_files = len(files_to_process)
        cpus_used = args.cpus
        with Pool(processes=cpus_used) as pool:
            values = list(tqdm(pool.imap(sanitize_mail, files_to_process),
                               total=nb_files, ncols=100, desc=f"Sanitizing {nb_files} files over {cpus_used} CPUs"))
        print("\n".join([f"{value}" for value in values if value is not None]))
        print("DONE !")
