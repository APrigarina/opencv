#!/usr/bin/env python

'''

This sample uses dataset from
http://www.fit.vutbr.cz/research/groups/graph/pclines/pub_page.php?id=2012-SCCG-QRtiles
and markup files located in markup/ folder
for evaluation QR-code detection algorithm

'''

# Python 2/3 compatibility
import optparse
from pathlib import Path

import cv2
import numpy as np
import json

evaluate_metrics = [
    "all_qrcodes",
    "one_qrcode",
    "all_qrcodes_in_category",
    "intersection_over_union",
    "f_score"
]

def main():
    parser = optparse.OptionParser()
    parser.add_option('--images', default="qrcode-datasets/datasets", help="Location of directory with input images")
    parser.add_option('--data', default="markup", help="Location of directory with input data")
    options, arguments = parser.parse_args()

    path_to_images = Path(options.images)
    path_to_data = Path(options.data)

    dir_images = [f for f in sorted(path_to_images.iterdir())]
    dir_data = [f for f in sorted(path_to_data.iterdir()) if f.is_file()]

    for metric in evaluate_metrics:
        run_metric_through_categories(dir_images, dir_data, metric)

def run_metric_through_categories(categories, dir_data, metric):
    print_metric_description(metric)

    detection_stat = []
    decoding_stat = []
    scores = []

    qrDetector = cv2.QRCodeDetector()

    for idx, path_to_category in enumerate(categories):
        category_score = []

        detected_in_category = 0
        decoded_in_category = 0

        number_qrcodes_in_category = get_number_qrcodes_in_category(dir_data[idx])

        input_images = get_input_images(path_to_category)
        input_data = get_input_data(dir_data[idx])

        total_number_images = len(input_data['test_images'])

        for path_to_image in input_images:
            current_image = path_to_image.name

            for img_infos in input_data['test_images']:
                if current_image == img_infos['image_name']:
                    image_data = img_infos

            image_to_detect = cv2.imread(str(path_to_image))

            if metric == "all_qrcodes":
                detected, decoded = compute_all_qrcodes(image_data, image_to_detect, qrDetector)
            elif metric == "one_qrcode":
                detected, decoded = compute_one_qrcode(image_to_detect, qrDetector)
            elif metric == "all_qrcodes_in_category":
                detected, decoded = compute_all_qrcodes_in_category(image_to_detect, qrDetector)
            elif metric == "intersection_over_union":
                score = compute_intersection_over_union(image_data, image_to_detect, qrDetector)
                if score > 0:
                    category_score.append(score)
            elif metric == "f_score":
                score = compute_f_score(image_data, image_to_detect, qrDetector)
                category_score.append(score)

            if metric in {"all_qrcodes", "one_qrcode", "all_qrcodes_in_category"}:
                detected_in_category += detected
                decoded_in_category += decoded

        if metric in {"all_qrcodes", "one_qrcode"}:
            detected_percent = detected_in_category/total_number_images
            detection_stat.append(detected_percent)

            decoded_percent = decoded_in_category/total_number_images
            decoding_stat.append(decoded_percent)
        elif metric == "all_qrcodes_in_category":
            detected_percent = detected_in_category/number_qrcodes_in_category
            detection_stat.append(detected_percent)

            decoded_percent = decoded_in_category/number_qrcodes_in_category
            decoding_stat.append(decoded_percent)
        else:
            scores.append(np.mean(category_score))

    if metric in {"all_qrcodes", "one_qrcode", "all_qrcodes_in_category"}:
        print_result(categories, detection_stat, decoding_stat)
    else:
        print_result_scores(categories, scores)


def get_input_images(path_to_category):
    extensions = {'*.jpg', '*.JPG', '*.png'}
    input_images = []
    for ext in extensions:
        input_images.extend(path_to_category.glob(ext))

    return input_images


def get_input_data(path_to_file):
    json_file = open(path_to_file, 'r')
    input_data = json.load(json_file)

    return input_data


def print_metric_description(metric):
    if metric == "all_qrcodes":
        print("The percentage of pictures in each category where all QR-codes on the picture are detected/decoded\n")
    elif metric == "one_qrcode":
        print("The percentage of pictures in each category where at least one QR-code on the picture is detected/decoded\n")
    elif metric == "all_qrcodes_in_category":
        print("The percentage of QR-codes detected/decoded among all QR-codes in each category\n")
    elif metric == "intersection_over_union":
        print("Intersection over Union\n")
    elif metric == "f_score":
        print("F1-score\n")


def get_number_qrcodes_in_category(input_file):
    number_qrcodes = 0

    input_data = get_input_data(input_file)
    total_number_images = len(input_data['test_images'])

    for idx in range(total_number_images):
        image_data = input_data['test_images'][idx]
        number_qrcodes += len(image_data['points'])

    return number_qrcodes


def print_result(categories, detection_stat, decoding_stat):
    for idx, category in enumerate(categories):
        print("Category {}".format(category.name))
        print("detected percent: {} %".format(np.round(detection_stat[idx] * 100, 2)))
        print("decoded percent: {} %\n".format(np.round(decoding_stat[idx] * 100, 2)))


def print_result_scores(categories, scores):
    for idx, category in enumerate(categories):
        print("Category {}".format(category.name))
        print("Score: {} %\n".format(np.round(scores[idx] * 100, 2)))


def compute_all_qrcodes(image_data, image_to_detect, qrDetector):
    detected = 0
    decoded = 0

    expected_number_qrcodes = len(image_data['points'])

    _, bboxes = qrDetector.detectMulti(image_to_detect)

    if bboxes is not None:
        if expected_number_qrcodes == len(bboxes):
            detected += 1

        _, decoded_data, _ = qrDetector.decodeMulti(image_to_detect, bboxes)

        if len(decoded_data) > 0:
            number_decoded = 0
            for data in decoded_data:
                if len(data) > 0:
                    number_decoded += 1
            if number_decoded == expected_number_qrcodes:
                decoded +=1

    return detected, decoded


def compute_one_qrcode(image_to_detect, qrDetector):
    detected = 0
    decoded = 0

    _, bboxes = qrDetector.detectMulti(image_to_detect)

    if bboxes is not None and len(bboxes) > 0:
        detected += 1

        _, decoded_data, _ = qrDetector.decodeMulti(image_to_detect, bboxes)

        if len(decoded_data) > 0:
            flag = False
            for data in decoded_data:
                if len(data) > 0:
                    flag = True
            if flag:
                decoded += 1

    return detected, decoded


def compute_all_qrcodes_in_category(image_to_detect, qrDetector):
    detected = 0
    decoded = 0

    _, bboxes = qrDetector.detectMulti(image_to_detect)

    if bboxes is not None:
        detected += len(bboxes)

        _, decoded_data, _ = qrDetector.decodeMulti(image_to_detect, bboxes)

        if len(decoded_data) > 0:
            for data in decoded_data:
                if len(data) > 0:
                    decoded += 1
    return detected, decoded


def list_to_points(points):
    result = []
    for i in range(0, len(points), 2):
        result.append((float(points[i]), float(points[i+1])))

    return result


def intersection_lines(a1, a2, b1, b2):
    c1 = ((a1[0] * a2[1]  -  a1[1] * a2[0]) * (b1[0] - b2[0]) \
       - (b1[0] * b2[1]  -  b1[1] * b2[0]) * (a1[0] - a2[0])) \
       / ((a1[0] - a2[0]) * (b1[1] - b2[1]) - (a1[1] - a2[1]) * (b1[0] - b2[0]))

    c2 = ((a1[0] * a2[1]  -  a1[1] * a2[0]) * (b1[1] - b2[1]) \
       - (b1[0] * b2[1]  -  b1[1] * b2[0]) * (a1[1] - a2[1])) \
       / ((a1[0] - a2[0]) * (b1[1] - b2[1]) - (a1[1] - a2[1]) * (b1[0] - b2[0]))

    return np.array([c1, c2])


def get_qrcodes_centers(points):
    data_centers = []
    for p in points:
        center = intersection_lines(p[0], p[2], p[1], p[3])
        data_centers.append(center)

    return data_centers


def get_corresponding_qrcodes(bbox_centers, true_points_centers):
    nearest_centers = []
    for bb_center in bbox_centers:
        distances = []
        for tp_center in true_points_centers:
            dist = cv2.norm(bb_center - tp_center)
            distances.append(dist)

        min_idx = np.argmin(distances)
        min_value = min(distances)
        nearest_centers.append(min_idx)

    return nearest_centers


def compute_intersection_over_union(image_data, image_to_detect, qrDetector):
    img_stat = 0
    temp_points = image_data['points']
    true_points = []

    for tmp in temp_points:
        true_points.append(list_to_points(tmp))
    true_points_centers = get_qrcodes_centers(true_points)

    _, bboxes = qrDetector.detectMulti(image_to_detect)

    size = image_to_detect.shape[:2]

    if bboxes is not None and len(bboxes) > 0:
        bbox_stat = 0

        bbox_centers = get_qrcodes_centers(bboxes)
        bbox_nearest_centers = get_corresponding_qrcodes(bbox_centers, true_points_centers)

        for idx, point in enumerate(bbox_nearest_centers):
            idx_bbox = idx
            idx_true_bbox = point

            detected_bbox = bboxes[idx]
            matched_true_bbox = true_points[idx_true_bbox]

            detect_mask = np.zeros(size, np.uint8)
            true_mask = np.zeros(size, np.uint8)

            cv2.fillPoly(detect_mask, np.array([detected_bbox], dtype=np.int32), (255))
            cv2.fillPoly(true_mask, np.array([matched_true_bbox], dtype=np.int32), (255))

            union = detect_mask | true_mask
            n_white_pix_union = np.sum(union == 255)

            inter = detect_mask & true_mask
            n_white_pix_inter = np.sum(inter == 255)

            iou = n_white_pix_inter / n_white_pix_union

            bbox_stat += iou

        img_stat = bbox_stat / len(bboxes)

    return img_stat


def compute_f_score(image_data, image_to_detect, qrDetector):
    tp = 0
    fp = 0
    fn = 0

    temp_points = image_data['points']
    true_points = []

    for tmp in temp_points:
        true_points.append(list_to_points(tmp))
    true_points_centers = get_qrcodes_centers(true_points)
    number_qrcodes = len(temp_points)

    _, bboxes = qrDetector.detectMulti(image_to_detect)

    size = image_to_detect.shape[:2]

    if bboxes is None:
        bboxes = []

    if len(bboxes) > 0:
        bbox_stat = 0

        bbox_centers = get_qrcodes_centers(bboxes)
        bbox_nearest_centers = get_corresponding_qrcodes(bbox_centers, true_points_centers)

        for idx, point in enumerate(bbox_nearest_centers):
            idx_bbox = idx
            idx_true_bbox = point

            detected_bbox = bboxes[idx]
            matched_true_bbox = true_points[idx_true_bbox]

            detect_mask = np.zeros(size, np.uint8)
            true_mask = np.zeros(size, np.uint8)

            cv2.fillPoly(detect_mask, np.array([detected_bbox], dtype=np.int32), (255))
            cv2.fillPoly(true_mask, np.array([matched_true_bbox], dtype=np.int32), (255))

            inter = detect_mask & true_mask
            n_white_pix_inter = np.sum(inter == 255)

            if n_white_pix_inter > 0:
                tp += 1
            else:
                fp += 1

    if len(bboxes) > number_qrcodes:
        fp += (len(bboxes) - number_qrcodes)
    elif len(bboxes) < number_qrcodes:
        fn += (number_qrcodes - len(bboxes))

    f_score = 0
    precision = 0
    recall = 0

    if tp + fp > 0:
        precision = tp / (tp + fp)
    if tp + fn > 0:
        recall = tp / (tp + fn)
    if precision + recall > 0:
        f_score = 2 * precision * recall / (precision + recall)

    return f_score


if __name__ == '__main__':
    main()
