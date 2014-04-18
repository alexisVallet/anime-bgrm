import os
import cv2
import saliency
import cvUtils
import numpy as np

def srsGrabcutBgRemoval(bgrImage):
    """ Runs background removal on an image using a combination of spectral residual
        saliency and grabcut. Parametrized to give good results on animation images.
    Args:
        bgrImage (array): bgr image to remove the background from.
    Returns:
        A mask with 1 for foreground and 0 for background, of the same size as the
        source image.
    """
    image = cv2.cvtColor(bgrImage, cv2.COLOR_BGR2GRAY)
    saliencyMap, resized = saliency.spectralResidualSaliency(image)
    protoObjects = saliency.saliencyThresh(saliencyMap)
    segmentation, background = cvUtils.connectedComponents(protoObjects)
    # generate a mask for the largest object in the image.
    charMask = cvUtils.generateMask(segmentation, segmentation.getLargestObject(),
                                    segVal = cv2.GC_PR_FGD, bgVal = cv2.GC_BGD)
    # Run grabcut to enhance the result
    bgModel, fgModel = [None] * 2
    rows, cols = resized.shape
    colorResized = cv2.resize(bgrImage, (cols, rows))
    cv2.grabCut(colorResized, charMask, None, bgModel, fgModel, 1)
    # Once again only keep the largest connected component
    cvMaskBool = np.equal(charMask, np.ones([rows, cols]) * cv2.GC_PR_FGD)
    cvMask = cvMaskBool.astype(np.float)
    segmentation2, background2 = cvUtils.connectedComponents(cvMask)
    finalMask = cvUtils.generateMask(segmentation2, segmentation2.getLargestObject())
    # Resize the mask to the original image size.
    originalRows, originalCols = bgrImage.shape[0:2]

    return cv2.resize(finalMask, (originalCols, originalRows))

if __name__ == "__main__":
    imageFolder = 'data/background'
    outputFolder = 'data/srs_grabcut_bgrm'
    imageNames = [f for f in sorted(os.listdir(imageFolder), key=str.lower)
                  if os.path.isfile(os.path.join(imageFolder, f)) 
                  and f.lower().endswith(('.png', '.jpg', '.gif'))]

    for imageName in imageNames:
        print 'Processing ' + imageName
        inputFilename = os.path.join(imageFolder, imageName)
        image = cv2.imread(inputFilename)
        mask = srsGrabcutBgRemoval(image)
        maskedImage = cvUtils.maskAsAlpha(image, mask)
        cv2.imwrite(os.path.join(outputFolder, os.path.splitext(imageName)[0] + '.png'),
                    maskedImage)