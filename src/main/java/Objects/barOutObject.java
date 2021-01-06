package Objects;

import java.util.ArrayList;

public class barOutObject {

    private String fileName;
    private String tag;
    private String ind1;
    private String ind2;
    private ArrayList<subFieldObject> subFieldList;

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    public String getTag() {
        return tag;
    }

    public void setTag(String tag) {
        this.tag = tag;
    }

    public String getInd1() {
        return ind1;
    }

    public void setInd1(String ind1) {
        this.ind1 = ind1;
    }

    public String getInd2() {
        return ind2;
    }

    public void setInd2(String ind2) {
        this.ind2 = ind2;
    }

    public ArrayList<subFieldObject> getSubFieldList() {
        return subFieldList;
    }

    public void setSubFieldList(ArrayList<subFieldObject> subFieldList) {
        this.subFieldList = subFieldList;
    }

    public barOutObject(String fileName, String tag, String ind1, String ind2, ArrayList<subFieldObject> subFieldList) {
        this.fileName = fileName;
        this.tag = tag;
        this.ind1 = ind1;
        this.ind2 = ind2;
        this.subFieldList = subFieldList;
    }
}
