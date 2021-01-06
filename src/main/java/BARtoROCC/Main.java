package BARtoROCC;




import BARObject.Collection;
import BARObject.Datafield;
import Objects.barOutObject;
import Objects.subFieldObject;
import Utilities.XMLCleaner.*;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBException;
import javax.xml.bind.Unmarshaller;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import static Utilities.XMLCleaner.XMLCleaner;

public class Main {
    public static void main(String[] args) throws JAXBException, IOException {





        XMLCleaner("original//exp_404829.xml", "input//exp_404829.xml");

        int ok1 = 1;



        JAXBContext context = JAXBContext.newInstance(Collection.class);
        Unmarshaller unMarshaller = context.createUnmarshaller();
        Collection barInput = (Collection) unMarshaller.unmarshal(new FileInputStream("input//exp_404829.xml"));

        ArrayList<barOutObject> myInputBarList = new ArrayList<>();



        for (int i = 0; i < barInput.getRecord().getDatafield().size(); i ++){
            ArrayList<subFieldObject> mySubFieldList = new ArrayList<>();
            for (int j = 0; j < barInput.getRecord().getDatafield().get(i).getSubfield().size();j++){
                mySubFieldList.add(new subFieldObject(
                        barInput.getRecord().getDatafield().get(i).getSubfield().get(j).getCode(),
                        barInput.getRecord().getDatafield().get(i).getSubfield().get(j).getContent()
                ));
            }
            myInputBarList.add(new barOutObject(
                    barInput.getRecord().getDatafield().get(i).getTag(),
                    barInput.getRecord().getDatafield().get(i).getInd1(),
                    barInput.getRecord().getDatafield().get(i).getInd2(),
                    mySubFieldList));

        }


        int ok =1;

    }


}
